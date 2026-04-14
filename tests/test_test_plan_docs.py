"""2단계 테스트 계획 문서가 저장소에 존재하는지 검증한다."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS_TEST_PLAN = ROOT / "docs" / "test-plan"

REQUIRED = [
    "README.md",
    "phase-a-feasibility.md",
    "phase-b-poc.md",
    "metrics-protocol.md",
    "legacy-test-mapping.md",
    "overlap-and-independent-readpath.md",
]


@pytest.mark.parametrize("name", REQUIRED)
def test_test_plan_doc_exists(name: str) -> None:
    path = DOCS_TEST_PLAN / name
    assert path.is_file(), f"missing: {path.relative_to(ROOT)}"


def test_metrics_protocol_mentions_p95_and_thresholds() -> None:
    text = (DOCS_TEST_PLAN / "metrics-protocol.md").read_text(encoding="utf-8")
    assert "p95" in text
    assert "0.95" in text or "95%" in text
    assert "300" in text
