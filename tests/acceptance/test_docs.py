"""Acceptance tests for the workforce operating guide and the first handoff."""
from pathlib import Path

import pytest

from tools.handoff_log import read_all

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "docs" / "workforce.md"
README = ROOT / "README.md"
LOG = ROOT / "workforce" / "status" / "handoffs.jsonl"
DESIGN = "docs/superpowers/specs/2026-10-19-ai-workforce-portfolio-design.md"


@pytest.fixture(scope="module")
def guide():
    assert GUIDE.exists(), f"missing {GUIDE}"
    return GUIDE.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "needle",
    ["Role:", "workforce/status/handoffs.jsonl", "tester sign-off", "employer", "Known limits"],
)
def test_guide_mentions(guide, needle):
    assert needle in guide


@pytest.mark.parametrize("role", ["manager", "developer", "tester", "deployer"])
def test_guide_names_each_role(guide, role):
    assert role in guide.lower()


def test_readme_links_guide_and_design_doc():
    text = README.read_text(encoding="utf-8")
    assert "docs/workforce.md" in text
    assert DESIGN in text


def test_first_handoff_recorded():
    entries = read_all(LOG)
    assert any(e.project == "foundation" for e in entries)
