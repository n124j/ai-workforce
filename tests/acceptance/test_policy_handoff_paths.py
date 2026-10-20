"""Every role may append to the handoff log; other status files stay manager-only."""
from pathlib import Path

import pytest

from tools.role_paths import load_policy, violations

ROOT = Path(__file__).resolve().parents[2]
POLICY = load_policy(ROOT / "workforce" / "policy.toml")
LOG = "workforce/status/handoffs.jsonl"
OTHER = "workforce/status/notes.md"


@pytest.mark.parametrize("role", ["manager", "developer", "tester", "deployer"])
def test_all_roles_may_touch_handoff_log(role):
    assert violations(role, [LOG], POLICY) == []


@pytest.mark.parametrize("role", ["developer", "tester", "deployer"])
def test_non_managers_may_not_touch_other_status_files(role):
    assert violations(role, [OTHER], POLICY) == [OTHER]


def test_manager_may_touch_other_status_files():
    assert violations("manager", [OTHER], POLICY) == []


def test_guide_known_limits_mentions_self_declared_from_role():
    text = (ROOT / "docs" / "workforce.md").read_text(encoding="utf-8")
    limits = text.split("## Known limits", 1)[1]
    assert "self-declared" in limits
    assert "from_role" in limits
