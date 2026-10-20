"""Acceptance tests for the four subagent definition files."""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
AGENTS = ROOT / ".claude" / "agents"
ROLES = ("manager", "developer", "tester", "deployer")
KEYS = ("name", "description", "tools", "model")
POLICY = tomllib.loads((ROOT / "workforce" / "policy.toml").read_text(encoding="utf-8"))["roles"]

HARD_RULES = {
    "tester": "cannot edit product source",
    "developer": "cannot mark its own work done",
    "deployer": "tester sign-off",
}


def parse(role: str) -> tuple[dict[str, str], str]:
    text = (AGENTS / f"{role}.md").read_text(encoding="utf-8")
    lines = text.splitlines()
    assert lines[0] == "---", "file must start with frontmatter"
    end = lines.index("---", 1)
    meta = {}
    for line in lines[1:end]:
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, "\n".join(lines[end + 1:])


@pytest.mark.parametrize("role", ROLES)
def test_file_exists_with_frontmatter(role):
    assert (AGENTS / f"{role}.md").is_file()
    meta, _ = parse(role)
    for key in KEYS:
        assert meta.get(key), f"missing frontmatter key {key}"
    assert meta["name"] == role


def test_manager_has_no_bash():
    meta, _ = parse("manager")
    tools = [t.strip() for t in meta["tools"].split(",")]
    assert "Bash" not in tools


@pytest.mark.parametrize("role", ROLES)
def test_body_has_trailer(role):
    _, body = parse(role)
    assert f"Role: {role}" in body


@pytest.mark.parametrize("role", ROLES)
def test_body_lists_every_policy_glob(role):
    _, body = parse(role)
    missing = [g for g in POLICY[role] if g not in body]
    assert not missing, f"{role} body omits policy globs: {missing}"


@pytest.mark.parametrize("role,phrase", sorted(HARD_RULES.items()))
def test_hard_rule_phrase(role, phrase):
    _, body = parse(role)
    assert phrase in body
