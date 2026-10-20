# Workforce Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the `ai-workforce` repo with four enforced agent roles (manager, developer, tester, deployer), an auditable handoff log, CI gates, and a thin portfolio hub site, so project 1 can start.

**Architecture:** Roles are Claude Code subagent definitions in `.claude/agents/`. Their boundaries are enforced by a path policy (`workforce/policy.toml`) checked in CI against each commit's `Role:` trailer. Handoffs are appended as JSONL to `workforce/status/`. The hub site is a static Astro site whose project list is validated data, so it cannot claim a project is shipped without a repo link.

**Tech Stack:** Python 3.12 + pytest (tools), Astro + TypeScript + Vitest (site), GitHub Actions, gitleaks.

**Spec:** `docs/superpowers/specs/2026-10-19-ai-workforce-portfolio-design.md` (sections 3, 4, 6, 8, 9). This is plan 1 of 7; plans for projects 1-5 and the site case studies follow separately.

## Global Constraints

- Free and local only: Docker, GitHub Actions, GitHub Pages. No paid cloud resources.
- No secrets in git; `.env.example` only; secret scanning in CI.
- No current or past employer IP, names, data, or metrics anywhere.
- No fabricated or inflated claims; site status values are `planned`, `in-progress`, `shipped` and `shipped` requires a repo URL.
- Nothing is pushed or published without Niraj's approval. GitHub remote: `https://github.com/n124j/ai-workforce.git`.
- Test-first. Python 3.12, stdlib only for runtime tools (`tomllib`, `json`, `subprocess`); pytest is the only dev dependency.
- Role path ownership (section 4 of spec, refined here): developer may not touch `tests/acceptance/**`, `evals/**`; tester may not touch product source; manager writes no product code; deployer ships only with tester sign-off.
- Commit messages end with the role trailer line `Role: <manager|developer|tester|deployer>`.

## Review Focus

1. Commit with no `Role:` trailer: must fail the CI check, not pass silently.
2. Renamed or deleted files: both old and new paths count as touched by the role.
3. Windows-style `\` paths and a root-level file (e.g. `README.md`) in the policy matching.
4. Merge commits and empty commits: checker must not crash and must skip merge commits.
5. Site project entry with `status: "shipped"` but empty `repo_url`, or an empty projects list: validation fails the first, renders an honest empty state for the second.

---

## File Structure

```
.claude/agents/{manager,developer,tester,deployer}.md   # subagent definitions
workforce/policy.toml                                    # role -> allowed path globs
workforce/status/handoffs.jsonl                          # append-only handoff trail
tools/role_paths.py                                      # policy checker (CLI + lib)
tools/handoff_log.py                                     # handoff append/validate
tools/hygiene.py                                         # repo hygiene checks
tests/unit/                                              # developer-owned unit tests
tests/acceptance/                                        # tester-owned acceptance tests
site/                                                    # Astro hub site
.github/workflows/{ci.yml,pages.yml}
docs/workforce.md                                        # how the loop runs
README.md  LICENSE  .gitignore  .env.example  pyproject.toml
```

### Task 1: Repo baseline and hygiene checker

**Files:**
- Create: `.gitignore`, `.env.example`, `LICENSE` (MIT, holder "Niraj Byanjankar"), `README.md`, `pyproject.toml`, `tools/__init__.py`, `tools/hygiene.py`
- Test: `tests/unit/test_hygiene.py`

**Interfaces:**
- Produces: `find_secret_like(text: str) -> list[str]` (returns matched token kinds, e.g. `"aws-access-key"`, `"private-key"`, `"generic-api-key"`); `check_repo(root: Path) -> list[str]` (list of human-readable problems, empty means clean).

- [ ] **Step 1: Write failing tests** in `tests/unit/test_hygiene.py`:
  - `test_flags_private_key_header`: `find_secret_like("-----BEGIN RSA PRIVATE KEY-----")` contains `"private-key"`.
  - `test_flags_aws_key`: `find_secret_like("AKIAABCDEFGHIJKLMNOP")` contains `"aws-access-key"`.
  - `test_ignores_plain_text`: `find_secret_like("hello world")` is `[]`.
  - `test_check_repo_requires_env_ignored`: a tmp repo whose `.gitignore` lacks `.env` returns a problem mentioning `.env`.
  - `test_check_repo_requires_env_example`: tmp repo with no `.env.example` returns a problem mentioning `.env.example`.
  - `test_check_repo_flags_secret_in_tracked_text_file`: tmp repo with `config.txt` containing an AWS key returns a problem naming `config.txt`.
  - `test_check_repo_clean`: a tmp repo with `.gitignore` (containing `.env`), `.env.example`, and benign files returns `[]`.
- [ ] **Step 2: Run** `python -m pytest tests/unit/test_hygiene.py -v`. Expected: FAIL (module missing).
- [ ] **Step 3: Implement** `tools/hygiene.py` per the signatures above. Use regexes for the three kinds; `check_repo` walks text files (skip `.git`, `node_modules`, binary files) and reports `<path>: <kind>`.
- [ ] **Step 4: Run** the same command. Expected: all PASS.
- [ ] **Step 5: Add baseline files.** `.gitignore` ignores `.env`, `.venv/`, `__pycache__/`, `node_modules/`, `site/dist/`, `.astro/`, `*.gguf`. `.env.example` holds placeholder names only (`OPENAI_API_KEY=`, `GEMINI_API_KEY=`, `ANTHROPIC_API_KEY=`, `OLLAMA_HOST=http://localhost:11434`), all empty. `README.md` states what the repo is and that projects live in separate repos. `pyproject.toml` pins `requires-python = ">=3.12"` and `pytest` as dev dependency.
- [ ] **Step 6: Run** `python -c "from pathlib import Path; from tools.hygiene import check_repo; print(check_repo(Path('.')))"`. Expected: `[]`.
- [ ] **Step 7: Commit** `chore: repo baseline and hygiene checker` with trailer `Role: developer`.

### Task 2: Role path policy and checker

**Files:**
- Create: `workforce/policy.toml`, `tools/role_paths.py`
- Test: `tests/unit/test_role_paths.py`

**Interfaces:**
- Produces:
  - `load_policy(path: Path) -> dict[str, list[str]]` (role -> glob list)
  - `role_from_trailer(message: str) -> str | None` (reads a final `Role: x` trailer line, case-insensitive key, lowercases value)
  - `violations(role: str, changed: list[str], policy: dict[str, list[str]]) -> list[str]` (paths not matched by the role's globs; normalizes `\` to `/`)
  - `main(argv: list[str]) -> int` CLI: `python -m tools.role_paths --base <rev> --head <rev> [--policy workforce/policy.toml]`; exit 0 clean, 1 violations or unknown/missing role.

`workforce/policy.toml` content (exact):

```toml
[roles]
manager   = ["docs/superpowers/**", "docs/workforce.md", "workforce/status/**", "workforce/backlog/**"]
developer = ["tools/**", "src/**", "site/src/**", "site/package.json", "tests/unit/**", "docs/adr/**", "README.md", "pyproject.toml", ".gitignore", ".env.example", "LICENSE"]
tester    = ["tests/acceptance/**", "evals/**", "site/tests/**"]
deployer  = [".github/**", "docker/**", "Dockerfile*", "compose*.yaml", "terraform/**", "site/astro.config.*"]
```

- [ ] **Step 1: Write failing tests** in `tests/unit/test_role_paths.py` (use `fnmatch`-style `**` semantics: `**` matches across `/`):
  - `test_trailer_parsed`: `role_from_trailer("feat: x\n\nRole: Tester")` == `"tester"`.
  - `test_missing_trailer_is_none`: `role_from_trailer("feat: x")` is `None`.
  - `test_developer_cannot_touch_acceptance_tests`: `violations("developer", ["tests/acceptance/test_a.py"], policy)` == `["tests/acceptance/test_a.py"]`.
  - `test_tester_cannot_touch_product_source`: `violations("tester", ["tools/hygiene.py"], policy)` == `["tools/hygiene.py"]`.
  - `test_tester_may_write_evals`: `violations("tester", ["evals/rag/golden.jsonl"], policy)` == `[]`.
  - `test_windows_separators`: `violations("developer", ["tools\\hygiene.py"], policy)` == `[]`.
  - `test_root_file_matches`: `violations("developer", ["README.md"], policy)` == `[]`.
  - `test_unknown_role_all_violations`: `violations("ceo", ["README.md"], policy)` == `["README.md"]`.
  - `test_cli_fails_on_missing_trailer` and `test_cli_skips_merge_commits`: build a tmp git repo with `git init`, make commits (one without trailer, one merge commit) and assert `main([...])` returns 1 and 0 respectively. For renames, assert both old and new path are checked (`git diff --name-status -M` parsed so both sides count).
- [ ] **Step 2: Run** `python -m pytest tests/unit/test_role_paths.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `tools/role_paths.py`. `main` lists commits in `base..head` with `git rev-list --no-merges`, reads each message via `git log -1 --format=%B`, gets changed paths via `git diff-tree --no-commit-id --name-status -r -M <sha>` (include both sides of renames/deletes), and prints one `sha role path` line per violation.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Create** `workforce/policy.toml` with the exact content above; add `test_policy_file_loads` asserting the four roles exist, then run it.
- [ ] **Step 6: Commit** `feat: role path policy and checker` with trailer `Role: developer`.

### Task 3: Handoff log

**Files:**
- Create: `tools/handoff_log.py`, `workforce/status/handoffs.jsonl` (empty), `workforce/backlog/.gitkeep`
- Test: `tests/unit/test_handoff_log.py`

**Interfaces:**
- Produces: `@dataclass(frozen=True) Handoff(project: str, from_role: str, to_role: str, summary: str, verdict: str, ts: str)` where `verdict` is one of `"submitted" | "approved" | "rejected" | "blocked"` and `ts` is ISO-8601 UTC; `append(log_path: Path, h: Handoff) -> None` (one JSON object per line, validates before writing); `read_all(log_path: Path) -> list[Handoff]`; `HandoffError(ValueError)`.

- [ ] **Step 1: Write failing tests:** appending then `read_all` round-trips; unknown role (`"ceo"`) raises `HandoffError`; unknown verdict raises `HandoffError`; empty `summary` raises `HandoffError`; a deployer handoff with verdict `"submitted"` and no prior tester `"approved"` for the same project raises `HandoffError` with `"tester sign-off"` in the message; two appends produce two lines (append-only, never rewrites).
- [ ] **Step 2: Run** `python -m pytest tests/unit/test_handoff_log.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `tools/handoff_log.py` per the interface. The deployer rule scans `read_all` for a `Handoff(from_role="tester", verdict="approved", project=h.project)` before accepting a deployer entry.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Commit** `feat: auditable handoff log` with trailer `Role: developer`.

### Task 4: Subagent definitions

**Files:**
- Create: `.claude/agents/manager.md`, `.claude/agents/developer.md`, `.claude/agents/tester.md`, `.claude/agents/deployer.md`
- Test: `tests/acceptance/test_agent_definitions.py`

**Interfaces:**
- Consumes: role names and path globs from `workforce/policy.toml` (Task 2), `append` from Task 3.
- Produces: four agent files, each with frontmatter `name`, `description`, `tools`, `model`, and a body stating: the role's job, its allowed paths (copied from the policy), the hard rule from spec section 4, the commit trailer it must use, and that it ends each task by recording a handoff via `tools.handoff_log`.

Tool allowlists: manager `Read, Grep, Glob, Write, Edit, Agent` (no Bash); developer `Read, Grep, Glob, Write, Edit, Bash`; tester `Read, Grep, Glob, Write, Edit, Bash`; deployer `Read, Grep, Glob, Write, Edit, Bash`. Model for all: `inherit`.

- [ ] **Step 1: Write failing acceptance tests** (tester-owned in execution): each of the four files exists and has frontmatter keys `name`, `description`, `tools`, `model`; `name` equals the file stem; manager's `tools` lacks `Bash`; each body contains its role's trailer line `Role: <name>`; each body lists every glob from that role's policy entry; the tester body contains the phrase `cannot edit product source`; the developer body contains `cannot mark its own work done`; the deployer body contains `tester sign-off`.
- [ ] **Step 2: Run** `python -m pytest tests/acceptance/test_agent_definitions.py -v`. Expected: FAIL.
- [ ] **Step 3: Write the four files** to satisfy the tests. Keep each under 60 lines.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Commit** (developer role for files; tester commits the test separately) `feat: manager, developer, tester, deployer agents` with the matching trailer for each commit.

### Task 5: CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`
- Test: `tests/acceptance/test_ci_workflow.py`

**Interfaces:**
- Consumes: `tools.hygiene.check_repo`, `tools.role_paths.main`, pytest suites.
- Produces: workflow `ci` on `pull_request` and `push` to `main` with jobs `python` (checkout with `fetch-depth: 0`; Python 3.12; `pip install pytest`; `pytest -q`; `python -m tools.role_paths --base ${{ github.event.pull_request.base.sha || github.event.before }} --head ${{ github.sha }}`; hygiene check), `secrets` (gitleaks via `gitleaks/gitleaks-action` pinned to a full commit SHA), `site` (Node 20; `npm ci`; `npm test`; `npm run build` inside `site/`). All third-party actions pinned to commit SHAs.

- [ ] **Step 1: Write failing tests:** parse the YAML with a minimal parser available in the test environment (add `pyyaml` to dev deps for tests only); assert jobs `python`, `secrets`, `site` exist; assert the `python` job's steps include one running `tools.role_paths` and one running `pytest`; assert `fetch-depth: 0` on checkout; assert every `uses:` ref other than local ones matches `@[0-9a-f]{40}`.
- [ ] **Step 2: Run** `python -m pytest tests/acceptance/test_ci_workflow.py -v`. Expected: FAIL.
- [ ] **Step 3: Write** `.github/workflows/ci.yml` to satisfy the tests (deployer role).
- [ ] **Step 4: Run** the same command. Expected: PASS. Then run `python -m pytest -q` for the full suite. Expected: all PASS.
- [ ] **Step 5: Commit** `ci: tests, role policy, hygiene, secret scan` with trailer `Role: deployer`.

### Task 6: Hub site skeleton with honest project data

**Files:**
- Create: `site/package.json`, `site/astro.config.mjs`, `site/tsconfig.json`, `site/src/data/projects.ts`, `site/src/pages/index.astro`, `site/src/lib/validateProjects.ts`
- Test: `site/tests/validateProjects.test.ts`

**Interfaces:**
- Produces in `site/src/lib/validateProjects.ts`: `type Status = "planned" | "in-progress" | "shipped"`; `type Project = { slug: string; title: string; summary: string; status: Status; repo_url: string }`; `validateProjects(projects: Project[]): string[]` (error list, empty means valid). Rules: slugs unique; `title` and `summary` non-empty; `status === "shipped"` requires `repo_url` starting with `https://github.com/n124j/`; `repo_url` must be empty for `planned`.
- `projects.ts` exports `projects: Project[]` with the five entries from spec section 5 (slugs `eval-first-rag`, `multi-agent-hitl`, `claude-code-agents`, `metadata-governance`, `llm-gateway`), all `status: "planned"`, `repo_url: ""`.
- `index.astro` renders the title "Niraj Byanjankar — Principal Software Engineer", a short factual intro (copy awaits Niraj's approval; placeholder text must read `[Copy pending approval]`), and the project list. Only `shipped` projects render as links; others render with a visible status label; an empty list renders the sentence "Projects are in progress." Calls `validateProjects` at build time and throws on any error.

- [ ] **Step 1: Write failing Vitest tests:** `test_shipped_requires_repo_url` (shipped + empty url yields an error containing `"repo_url"`); `test_duplicate_slugs`; `test_planned_with_url_is_invalid`; `test_empty_list_is_valid` (returns `[]`); `test_default_projects_valid` (imports `projects` and expects `[]`); `test_non_owner_url_rejected` (`https://github.com/other/x` for a shipped project errors).
- [ ] **Step 2: Run** `cd site && npm test`. Expected: FAIL (module missing). Scaffold `package.json` with `astro` and `vitest` pinned to exact versions chosen at install time, scripts `dev`, `build` (`astro build`), `test` (`vitest run`).
- [ ] **Step 3: Implement** `validateProjects.ts`, `projects.ts`, `index.astro`, `astro.config.mjs` (`site: "https://n124j.github.io"`, `base: "/ai-workforce"`).
- [ ] **Step 4: Run** `cd site && npm test && npm run build`. Expected: tests PASS, build succeeds, `site/dist/index.html` contains `Projects` and does not contain the word `shipped` as a link.
- [ ] **Step 5: Commit** `feat: hub site skeleton with validated project data` with trailer `Role: developer` (tester commits `site/tests/` separately with `Role: tester`; deployer commits `site/astro.config.mjs` with `Role: deployer`).

### Task 7: Pages deploy workflow (gated)

**Files:**
- Create: `.github/workflows/pages.yml`
- Test: `tests/acceptance/test_pages_workflow.py`

**Interfaces:**
- Produces: workflow `pages` triggered only by `workflow_dispatch` (never on push), with `permissions: { contents: read, pages: write, id-token: write }`, a `build` job (Node 20, `npm ci`, `npm run build` in `site/`, upload artifact from `site/dist`) and a `deploy` job using environment `github-pages`. Actions pinned to commit SHAs.

- [ ] **Step 1: Write failing tests:** the `on` block contains only `workflow_dispatch`; permissions are exactly the three above; every third-party `uses:` is SHA-pinned; deploy job references environment `github-pages`.
- [ ] **Step 2: Run** `python -m pytest tests/acceptance/test_pages_workflow.py -v`. Expected: FAIL.
- [ ] **Step 3: Write** `.github/workflows/pages.yml` (deployer role).
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Commit** `ci: gated pages deploy` with trailer `Role: deployer`.

### Task 8: Workforce operating guide and first handoff

**Files:**
- Create: `docs/workforce.md`
- Modify: `README.md` (link the guide and the design doc)
- Test: `tests/acceptance/test_docs.py`

**Interfaces:**
- Consumes: policy (Task 2), handoff log (Task 3), agents (Task 4), CI (Task 5).
- Produces: `docs/workforce.md` describing the per-project loop from spec section 4, how to dispatch each agent, the commit-trailer convention, how to read the handoff log, the approval gates (first push, public repos, cloud spend, publication), and the employer-IP rule. Also appends the first handoff `Handoff("foundation", "developer", "tester", "Workforce foundation complete; ready for acceptance review", "submitted", <now UTC>)`.

- [ ] **Step 1: Write failing tests:** `docs/workforce.md` exists and mentions each of `Role:` trailer, `workforce/status/handoffs.jsonl`, `tester sign-off`, `employer`, and the four role names; `README.md` links to `docs/workforce.md` and to the design doc path.
- [ ] **Step 2: Run** `python -m pytest tests/acceptance/test_docs.py -v`. Expected: FAIL.
- [ ] **Step 3: Write** the guide (manager role) and update `README.md`.
- [ ] **Step 4: Run** `python -m pytest -q`. Expected: whole suite PASS. Also run `python -m tools.role_paths --base <first-commit-sha> --head HEAD`. Expected: exit 0.
- [ ] **Step 5: Commit** `docs: workforce operating guide` with trailer `Role: manager`.
- [ ] **Step 6: Approval gate, do not skip.** Ask Niraj to approve adding the remote and the first push to `https://github.com/n124j/ai-workforce.git`. Only after an explicit yes: `git remote add origin <url>` and `git push -u origin <branch>`. Then, only with a second explicit yes, run the `pages` workflow.

---

## Self-Review

- **Spec coverage:** section 3 constraints (Global Constraints, Tasks 1, 7, 8 gate); section 4 roles and hard rules (Tasks 2, 3, 4); section 4 enforcement call in section 8 (policy, trailers, status log: Tasks 2, 3, 5); section 6 quality bar (CI, hygiene, secrets: Tasks 1, 5); site honesty and early scaffold (Task 6, 7); open items resolved in section 9 (remote URL, vertical plan). Projects 1-5 are intentionally out of scope for this plan.
- **Type consistency:** `Handoff` fields and role names match between Tasks 3, 4, 8; policy role keys (`manager`, `developer`, `tester`, `deployer`) match the agent file stems and trailer values.
- **Known tradeoff:** developer writes unit tests (`tests/unit/**`) while the tester owns `tests/acceptance/**` and `evals/**`; this reconciles "test-first" with "independent tester" and is a designer's call to confirm.
