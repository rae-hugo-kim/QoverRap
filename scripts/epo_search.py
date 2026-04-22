#!/usr/bin/env python3
"""EPO OPS v3.2 prior-art CQL search.

Usage:
  python scripts/epo_search.py                    # P1+P2 queries (default)
  python scripts/epo_search.py --all              # include P3
  python scripts/epo_search.py --query Q1 Q3      # specific queries

Inputs: .env must define EPO_OPS_KEY and EPO_OPS_SECRET.
Outputs: docs/research/epo-results-{group}.json + epo-quota-log.json.

Spec: docs/research/epo-queries.md.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "docs" / "research"
QUOTA_LOG_PATH = OUTPUT_DIR / "epo-quota-log.json"

AUTH_URL = "https://ops.epo.org/3.2/auth/accesstoken"
SEARCH_URL = "https://ops.epo.org/3.2/rest-services/published-data/search"

MIN_INTERVAL_SEC = 5.0  # search bucket is ~15/min; 4s+ interval keeps us under


@dataclass
class Query:
    id: str
    priority: str  # "P1" | "P2" | "P3"
    group: str     # "cn" | "ep-fr" | "jp" | "common"
    cql: str
    range: str     # e.g. "1-100"
    rationale: str
    country_filter: str | None = None  # post-hoc filter; EPO rejects pn=CN*/JP* (min 3 chars before *)


QUERIES: list[Query] = [
    # §3-1 CNIPA (pn=CN* not valid CQL — EPO requires ≥3 chars before *, filter client-side)
    Query("Q1", "P1", "cn", "in=(liu AND (fu OR yu)) AND cpc=G06K19/06", "1-100",
          "Liu et al. (2019) CN parallels"),
    Query("Q2", "P2", "cn", 'ti,ab=("rich QR" OR "three-layer QR")', "1-25",
          "Rich/three-layer QR titles (CN)", country_filter="CN"),
    Query("Q3", "P1", "cn", "ti,ab=(QR AND hamming)", "1-100",
          "Hamming-based QR (Liu core)", country_filter="CN"),
    Query("Q4", "P2", "cn", "ti,ab=(QR AND (steganograph* OR hidden))", "1-100",
          "Steganography QR CN", country_filter="CN"),
    # §3-2 INPI/EP
    Query("Q5", "P3", "ep-fr", "in=(tkachenko OR puech)", "1-100",
          "2LQR inventors"),
    Query("Q6", "P3", "ep-fr", 'pa=(CNRS OR "universite de montpellier" OR LIRMM) AND ti,ab=QR', "1-100",
          "2LQR institutions"),
    Query("Q7", "P3", "ep-fr", 'ti,ab=("two-level QR" OR "2LQR" OR "two level QR")', "1-25",
          "2LQR title keywords"),
    Query("Q8", "P3", "ep-fr", 'ti,ab=(QR AND (texture OR "print-and-scan" OR "P&S"))', "1-100",
          "2LQR technique keywords"),
    # §3-3 JP
    Query("Q9", "P3", "jp", 'pa=("denso wave" OR "denso corporation")', "1-100",
          "DENSO applicants"),
    Query("Q10", "P3", "jp", 'in=("masahiro hara")', "1-100",
          "QR origin inventor"),
    Query("Q11", "P2", "jp", 'ti,ab=(QR AND (multi-layer OR multilayer OR "multiple layer"))', "1-100",
          "Multi-layer QR JP", country_filter="JP"),
    Query("Q12", "P2", "jp", 'ti,ab=(QR AND (steganograph* OR "hidden data" OR payload))', "1-100",
          "Steganography/payload QR JP", country_filter="JP"),
    # §3-4 Common
    Query("Q13", "P2", "common", "cpc=G06K19/06 AND ti,ab=(signature AND QR)", "1-100",
          "QR + signature (Layer C)"),
    Query("Q14", "P2", "common", "ti,ab=(QR AND ed25519)", "1-100",
          "QR + ed25519 (exact match risk)"),
    Query("Q15", "P3", "common", 'ti,ab=(QR AND (delimiter OR "payload structur*"))', "1-100",
          "Payload structuring"),
]


@dataclass
class QuotaEntry:
    query_id: str
    priority: str
    status: str
    total_results: str | None
    throttling: str | None
    week_quota_used: str | None
    hour_quota_used: str | None
    retrieved: int = 0
    error: str | None = None


def get_token(key: str, secret: str) -> str:
    auth = base64.b64encode(f"{key}:{secret}".encode()).decode()
    r = requests.post(
        AUTH_URL,
        headers={"Authorization": f"Basic {auth}",
                 "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials"},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def run_search(token: str, cql: str, rng: str) -> tuple[requests.Response, str]:
    r = requests.get(
        SEARCH_URL,
        params={"q": cql, "Range": rng},
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        timeout=30,
    )
    return r, token


def extract_publications(body: dict) -> list[dict]:
    wpd = body.get("ops:world-patent-data", {})
    biblio = wpd.get("ops:biblio-search", {})
    sr = biblio.get("ops:search-result", {})
    refs = sr.get("ops:publication-reference", [])
    if isinstance(refs, dict):
        refs = [refs]
    out = []
    for ref in refs:
        docs = ref.get("document-id")
        if not docs:
            continue
        if isinstance(docs, dict):
            docs = [docs]
        for d in docs:
            if d.get("@document-id-type") != "docdb":
                continue
            out.append({
                "country": _get(d, "country"),
                "doc_number": _get(d, "doc-number"),
                "kind": _get(d, "kind"),
                "date": _get(d, "date"),
                "family_id": ref.get("@family-id"),
            })
            break
    return out


def _get(obj: dict, key: str) -> str | None:
    v = obj.get(key)
    if isinstance(v, dict):
        return v.get("$")
    return v


def run_query(token: str, q: Query) -> tuple[dict, QuotaEntry, str]:
    r, token = run_search(token, q.cql, q.range)
    throttle = r.headers.get("X-Throttling-Control")
    week = r.headers.get("X-RegisteredQuotaPerWeek-Used")
    hour = r.headers.get("X-IndividualQuotaPerHour-Used")
    entry_kwargs = dict(
        query_id=q.id, priority=q.priority,
        throttling=throttle, week_quota_used=week, hour_quota_used=hour,
    )

    if r.status_code == 403:
        return ({"query_id": q.id, "error": f"403: {r.text[:200]}"},
                QuotaEntry(status="403", total_results=None, error=r.text[:200], **entry_kwargs),
                token)
    if r.status_code == 401:
        return ({"query_id": q.id, "error": "401 auth"},
                QuotaEntry(status="401", total_results=None, error="auth", **entry_kwargs),
                token)
    if r.status_code == 404:
        # EPO returns 404 when no results
        return ({"query_id": q.id, "cql": q.cql, "range": q.range,
                 "total_results": "0", "publications": []},
                QuotaEntry(status="404-noresults", total_results="0", retrieved=0, **entry_kwargs),
                token)
    if r.status_code >= 400:
        return ({"query_id": q.id, "error": f"HTTP {r.status_code}: {r.text[:300]}"},
                QuotaEntry(status=str(r.status_code), total_results=None,
                           error=r.text[:200], **entry_kwargs),
                token)

    body = r.json()
    biblio = body.get("ops:world-patent-data", {}).get("ops:biblio-search", {})
    total = biblio.get("@total-result-count")
    pubs = extract_publications(body)
    filtered = [p for p in pubs if p.get("country") == q.country_filter] if q.country_filter else pubs
    result = {
        "query_id": q.id,
        "priority": q.priority,
        "group": q.group,
        "cql": q.cql,
        "range": q.range,
        "rationale": q.rationale,
        "country_filter": q.country_filter,
        "total_results": total,
        "retrieved_raw": len(pubs),
        "retrieved": len(filtered),
        "publications": filtered,
    }
    return (result,
            QuotaEntry(status="ok", total_results=total, retrieved=len(filtered), **entry_kwargs),
            token)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="include P3 queries")
    parser.add_argument("--query", nargs="+", metavar="QID",
                        help="run specific query IDs (e.g. Q1 Q3)")
    args = parser.parse_args()

    load_dotenv(REPO_ROOT / ".env")
    key = os.environ.get("EPO_OPS_KEY")
    secret = os.environ.get("EPO_OPS_SECRET")
    if not (key and secret):
        print("ERROR: EPO_OPS_KEY / EPO_OPS_SECRET missing in .env", file=sys.stderr)
        return 1

    if args.query:
        selected = [q for q in QUERIES if q.id in args.query]
    elif args.all:
        selected = QUERIES
    else:
        selected = [q for q in QUERIES if q.priority in ("P1", "P2")]

    print(f"Fetching token...")
    token = get_token(key, secret)
    print(f"Token OK. Running {len(selected)} queries.")

    grouped: dict[str, list[dict]] = {}
    quota_log: list[dict] = []
    halted = False

    for q in selected:
        print(f"  [{q.id}/{q.priority}/{q.group}] {q.cql[:70]}{'...' if len(q.cql) > 70 else ''}")
        try:
            result, qentry, token = run_query(token, q)
        except requests.RequestException as e:
            print(f"    NETWORK ERROR: {e}")
            quota_log.append({"query_id": q.id, "status": "network-error", "error": str(e)})
            time.sleep(MIN_INTERVAL_SEC)
            continue

        grouped.setdefault(q.group, []).append(result)
        quota_log.append(qentry.__dict__)
        print(f"    status={qentry.status} total={qentry.total_results} "
              f"got={qentry.retrieved} throttle={qentry.throttling}")

        if qentry.throttling and "black" in (qentry.throttling or "").lower():
            print("    BLACK throttle state — halting.")
            halted = True
            break
        if qentry.status == "403":
            print("    403 — halting.")
            halted = True
            break

        time.sleep(MIN_INTERVAL_SEC)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for group, results in grouped.items():
        path = OUTPUT_DIR / f"epo-results-{group}.json"
        path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved: {path.relative_to(REPO_ROOT)}")

    QUOTA_LOG_PATH.write_text(json.dumps(quota_log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {QUOTA_LOG_PATH.relative_to(REPO_ROOT)}")

    return 2 if halted else 0


if __name__ == "__main__":
    sys.exit(main())
