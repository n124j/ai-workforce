"""Acceptance tests for the CI workflow definition."""
import re
from pathlib import Path

import pytest
import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


@pytest.fixture(scope="module")
def wf():
    assert WORKFLOW.exists(), f"missing {WORKFLOW}"
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _steps(job):
    return job.get("steps", [])


def _runs(job):
    return [s["run"] for s in _steps(job) if "run" in s]


def test_workflow_name(wf):
    assert wf["name"] == "ci"


def test_triggers_include_pull_request_and_push_to_main(wf):
    # PyYAML (YAML 1.1) parses the key `on` as boolean True.
    triggers = wf.get("on", wf.get(True))
    assert triggers is not None
    assert "pull_request" in triggers
    assert "push" in triggers
    assert triggers["push"]["branches"] == ["main"]


def test_permissions_read_only(wf):
    assert wf["permissions"] == {"contents": "read"}


def test_required_jobs_exist(wf):
    assert {"python", "secrets", "site"} <= set(wf["jobs"])


def test_python_job_runs_pytest_and_role_paths(wf):
    runs = _runs(wf["jobs"]["python"])
    assert any("pytest" in r for r in runs)
    assert any("tools.role_paths" in r for r in runs)
    assert any("tools.hygiene" in r for r in runs)
    role = next(r for r in runs if "tools.role_paths" in r)
    assert "github.event.pull_request.base.sha || github.event.before" in role
    assert "--head ${{ github.sha }}" in role


def test_python_job_uses_python_312(wf):
    setups = [s for s in _steps(wf["jobs"]["python"])
              if s.get("uses", "").startswith("actions/setup-python@")]
    assert setups and str(setups[0]["with"]["python-version"]) == "3.12"


def _checkouts(job):
    return [s for s in _steps(job) if s.get("uses", "").startswith("actions/checkout@")]


@pytest.mark.parametrize("job", ["python", "secrets"])
def test_full_history_checkout(wf, job):
    checkouts = _checkouts(wf["jobs"][job])
    assert checkouts
    assert all(str(c["with"]["fetch-depth"]) == "0" for c in checkouts)


def test_secrets_job_runs_gitleaks(wf):
    steps = _steps(wf["jobs"]["secrets"])
    assert any(s.get("uses", "").startswith("gitleaks/gitleaks-action@") for s in steps)


def test_site_job_commands(wf):
    job = wf["jobs"]["site"]
    runs = _runs(job)
    for cmd in ("npm ci", "npm test", "npm run build"):
        assert cmd in runs
    for s in _steps(job):
        if "run" in s:
            assert s.get("working-directory") == "site"


def test_all_third_party_actions_pinned_to_sha(wf):
    refs = [s["uses"] for job in wf["jobs"].values() for s in _steps(job) if "uses" in s]
    assert refs
    for ref in refs:
        if ref.startswith("./"):
            continue
        assert re.search(r"@[0-9a-f]{40}$", ref), f"not SHA-pinned: {ref}"
