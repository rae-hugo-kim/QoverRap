#!/usr/bin/env python3
"""KIPRIS Plus prior-art keyword search.

Endpoint spec (verified by live probe 2026-04-17):
  base  : http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice
  op    : getAdvancedSearch
  param : ServiceKey, word, patent, utility, numOfRows, pageNo

Usage:
  python scripts/kipris_search.py                  # run default keyword set
  python scripts/kipris_search.py "키워드1" "키워드2"
"""
from __future__ import annotations

import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "docs" / "research"
OUTPUT_PATH = OUTPUT_DIR / "kipris-results.json"

BASE_URL = "http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch"

DEFAULT_KEYWORDS = [
    "QR코드 다층",
    "QR코드 서명",
    "QR코드 계층",
    "QR코드 접근 제어",
    "이차원코드 복수 레이어",
    "QR코드 오버래핑",
]

# Title-focused searches: narrower, higher precision
TITLE_KEYWORDS = [
    "다층 QR",
    "다중 QR",
    "QR 레이어",
    "QR 계층",
    "QR 서명",
    "QR 스테가노",
    "이중 QR",
    "중첩 QR",
    "비밀 QR",
    "은닉 QR",
    "QR 인증",
]


def search(word: str, access_key: str, num_rows: int = 100, *,
           field: str = "word") -> dict:
    """Run one keyword search against getAdvancedSearch.

    field: "word" (free text across all fields) or "inventionTitle" (title only)
    """
    params = {
        field: word,
        "patent": "true",
        "utility": "true",
        "numOfRows": num_rows,
        "pageNo": 1,
        "ServiceKey": access_key,
    }
    url = f"{BASE_URL}?{urlencode(params)}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return parse_xml(resp.text)


def parse_xml(xml_text: str) -> dict:
    """Parse getAdvancedSearch XML response into a dict."""
    root = ET.fromstring(xml_text)
    # Header (result code/msg) lives under header or at the top of body
    result_code = _first_text(root, ".//resultCode") or _first_text(root, ".//successYN")
    result_msg = _first_text(root, ".//resultMsg")
    total = _first_text(root, ".//totalCount") or _first_text(root, ".//TotalSearchCount")

    items = []
    for item in root.iter("item"):
        items.append({
            "inventionTitle": _first_text(item, "inventionTitle"),
            "applicationNumber": _first_text(item, "applicationNumber"),
            "applicationDate": _first_text(item, "applicationDate"),
            "registerNumber": _first_text(item, "registerNumber"),
            "registerDate": _first_text(item, "registerDate"),
            "openNumber": _first_text(item, "openNumber"),
            "openDate": _first_text(item, "openDate"),
            "ipcNumber": _first_text(item, "ipcNumber"),
            "applicantName": _first_text(item, "applicantName"),
            "abstract": _first_text(item, "astrtCont"),
            "registerStatus": _first_text(item, "registerStatus"),
        })

    return {
        "resultCode": result_code,
        "resultMsg": result_msg,
        "totalCount": int(total) if total and total.isdigit() else total,
        "items": items,
    }


def _first_text(node: ET.Element, tag: str) -> str | None:
    el = node.find(tag)
    return el.text.strip() if el is not None and el.text else None


def main() -> int:
    load_dotenv(REPO_ROOT / ".env")
    access_key = os.environ.get("KIPRIS_API_KEY")
    if not access_key:
        print("ERROR: KIPRIS_API_KEY not set in .env", file=sys.stderr)
        return 1

    args = sys.argv[1:]
    title_mode = "--title" in args
    if title_mode:
        args.remove("--title")
    field = "inventionTitle" if title_mode else "word"
    keywords = args or (TITLE_KEYWORDS if title_mode else DEFAULT_KEYWORDS)
    print(f"Running {len(keywords)} search(es) on field={field}...")

    results = []
    for kw in keywords:
        print(f"  search: {kw!r} ... ", end="", flush=True)
        try:
            payload = search(kw, access_key, field=field)
            print(f"total={payload['totalCount']} items={len(payload['items'])} code={payload['resultCode']}")
            results.append({"keyword": kw, "field": field, **payload})
        except requests.HTTPError as e:
            print(f"HTTP error: {e}")
            results.append({"keyword": kw, "field": field, "error": str(e)})
        except ET.ParseError as e:
            print(f"XML parse error: {e}")
            results.append({"keyword": kw, "field": field, "error": f"parse: {e}"})
        time.sleep(0.3)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / (
        "kipris-results-title.json" if title_mode else "kipris-results.json"
    )
    out_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nSaved: {out_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
