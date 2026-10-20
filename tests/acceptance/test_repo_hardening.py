"""Acceptance tests for dependency pinning, CODEOWNERS, policy owners and agent snippets."""
import tomllib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
POLICY = tomllib.loads((ROOT / "workforce" / "policy.toml").read_text(encoding="utf-8"))["roles"]
ROLES = ("manager", "developer", "tester", "deployer")


def test_requirements_dev_pins_exactly():
    path = ROOT / "requirements-dev.txt"
    assert path.is_file()
    lines = [x.strip() for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert lines == ["pytest==9.1.1", "PyYAML==6.0.3"]


def test_dependabot_weekly_for_three_ecosystems():
    path = ROOT / ".github" / "dependabot.yml"
    assert path.is_file()
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert cfg["version"] == 2
    found = {(u["package-ecosystem"], u["directory"]): u["schedule"]["interval"]
             for u in cfg["updates"]}
    assert found == {("pip", "/"): "weekly", ("npm", "/site"): "weekly",
                     ("github-actions", "/"): "weekly"}


@pytest.mark.parametrize("path", [
    "/workforce/policy.toml", "/.claude/agents/", "/tools/role_paths.py",
    "/tools/handoff_log.py", "/.github/",
])
def test_codeowners_lists_path(path):
    f = ROOT / ".github" / "CODEOWNERS"
    assert f.is_file()
    rows = [ln.split() for ln in f.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")]
    assert any(r[0] == path and "@n124j" in r[1:] for r in rows), path


def test_gitleaks_allowlist_for_fake_key():
    cfg = tomllib.loads((ROOT / ".gitleaks.toml").read_text(encoding="utf-8"))
    assert cfg["extend"]["useDefault"] is True
    assert "AKIAABCDEFGHIJKLMNOP" in "".join(cfg["allowlist"]["regexes"])


@pytest.mark.parametrize("role,glob", [
    ("developer", "site/public/**"), ("developer", "tests/conftest.py"),
    ("developer", "requirements*.txt"), ("deployer", ".gitleaks*"),
])
def test_policy_owns_previously_unowned_paths(role, glob):
    assert glob in POLICY[role]


def test_settings_local_is_gitignored():
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".claude/settings.local.json" in lines


@pytest.mark.parametrize("role", ROLES)
def test_agent_handoff_snippet_uses_current_time(role):
    body = (ROOT / ".claude" / "agents" / f"{role}.md").read_text(encoding="utf-8")
    assert "2026-10-19T12:00:00" not in body
    assert "datetime.now(timezone.utc).isoformat()" in body
