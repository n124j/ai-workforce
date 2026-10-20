"""Acceptance tests for the gated Pages deploy workflow definition."""
import re
from pathlib import Path

import pytest
import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "pages.yml"


@pytest.fixture(scope="module")
def wf():
    assert WORKFLOW.exists(), f"missing {WORKFLOW}"
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _steps(job):
    return job.get("steps", [])


def test_only_workflow_dispatch_trigger(wf):
    # PyYAML (YAML 1.1) parses the key `on` as boolean True.
    triggers = wf.get("on", wf.get(True))
    assert triggers is not None
    names = {triggers} if isinstance(triggers, str) else set(triggers)
    assert names == {"workflow_dispatch"}


def test_workflow_permissions_contents_read_only(wf):
    assert wf["permissions"] == {"contents": "read"}


def test_deploy_job_permissions_exactly_pages_and_id_token(wf):
    assert wf["jobs"]["deploy"]["permissions"] == {"pages": "write", "id-token": "write"}


def test_build_job_has_no_pages_or_id_token_permission(wf):
    perms = wf["jobs"]["build"].get("permissions", {})
    assert "id-token" not in perms and "pages" not in perms


def test_checkouts_do_not_persist_credentials(wf):
    checkouts = [s for job in wf["jobs"].values() for s in _steps(job)
                 if s.get("uses", "").startswith("actions/checkout@")]
    assert checkouts
    assert all(c["with"]["persist-credentials"] is False for c in checkouts)


def test_concurrency_group_pages_no_cancel(wf):
    assert wf["concurrency"] == {"group": "pages", "cancel-in-progress": False}


def test_all_third_party_actions_pinned_to_sha(wf):
    refs = [s["uses"] for job in wf["jobs"].values() for s in _steps(job) if "uses" in s]
    assert refs
    for ref in refs:
        if ref.startswith("./"):
            continue
        assert re.search(r"@[0-9a-f]{40}$", ref), f"not SHA-pinned: {ref}"


def test_jobs_are_build_and_deploy(wf):
    assert set(wf["jobs"]) == {"build", "deploy"}


def test_deploy_needs_build(wf):
    needs = wf["jobs"]["deploy"]["needs"]
    needs = [needs] if isinstance(needs, str) else needs
    assert "build" in needs


def test_deploy_environment_github_pages(wf):
    env = wf["jobs"]["deploy"]["environment"]
    assert env["name"] == "github-pages"
    assert env["url"] == "${{ steps.deployment.outputs.page_url }}"


def test_deploy_step_uses_deploy_pages_with_id(wf):
    steps = [s for s in _steps(wf["jobs"]["deploy"])
             if s.get("uses", "").startswith("actions/deploy-pages@")]
    assert len(steps) == 1
    assert steps[0]["id"] == "deployment"


def test_build_npm_steps_run_in_site(wf):
    npm_steps = [s for s in _steps(wf["jobs"]["build"])
                 if s.get("run", "").startswith("npm ")]
    assert {s["run"] for s in npm_steps} == {"npm ci", "npm test", "npm run build"}
    for s in npm_steps:
        assert s.get("working-directory") == "site"


def test_build_uploads_site_dist(wf):
    ups = [s for s in _steps(wf["jobs"]["build"])
           if s.get("uses", "").startswith("actions/upload-pages-artifact@")]
    assert len(ups) == 1
    assert ups[0]["with"]["path"] == "site/dist"


def test_build_uses_node_22(wf):
    setups = [s for s in _steps(wf["jobs"]["build"])
              if s.get("uses", "").startswith("actions/setup-node@")]
    assert setups and str(setups[0]["with"]["node-version"]) == "22"
