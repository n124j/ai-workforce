# Workforce operating guide

## What the workforce is

Four Claude Code subagents, defined in `.claude/agents/`, that build the portfolio projects
under one human director, Niraj Byanjankar. Each has its own file, its own path rules and its own
slice of the work. Rules live in `workforce/policy.toml`; progress is recorded in
`workforce/status/handoffs.jsonl`. Everything is free and local.

## The four roles

Paths come from `workforce/policy.toml`. A role must not touch anything outside its list.

| Role | May edit | Job |
|------|----------|-----|
| manager | `docs/superpowers/**`, `docs/workforce.md`, `workforce/status/**`, `workforce/backlog/**`, `workforce/policy.toml`, `.claude/agents/**` | Spec, acceptance criteria, backlog, gating handoffs, escalation. Writes no product code. |
| developer | `tools/**`, `src/**`, `site/src/**`, `site/package.json`, `site/tsconfig.json`, `site/package-lock.json`, `site/vitest.config.*`, `tests/unit/**`, `docs/adr/**`, `README.md`, `pyproject.toml`, `.gitattributes`, `.gitignore`, `.env.example`, `LICENSE` | Builds one slice at a time, with unit tests. |
| tester | `tests/acceptance/**`, `evals/**`, `site/tests/**` | Verifies independently. Rejects broken work rather than fixing product source. |
| deployer | `.github/**`, `docker/**`, `Dockerfile*`, `compose*.yaml`, `terraform/**`, `site/astro.config.*` | Packaging, CI, Pages, releases. |

## The per-project loop

1. Manager writes the spec and acceptance criteria.
2. Developer builds a slice.
3. Tester verifies it against the acceptance criteria.
4. Manager gates: accept, or send back.
5. Repeat for the next slice.
6. Deployer ships, only after tester sign-off (and director approval for anything public).

Design background: `docs/superpowers/specs/2026-10-19-ai-workforce-portfolio-design.md`
(section 4 for the loop, section 3 for approvals).

## Commit trailers

Every commit message ends with the role line, then the co-author line:

```
Role: developer
Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
```

CI runs `python -m tools.role_paths`, which fails any commit that has no `Role:` trailer, or whose
role may not touch one of the files in the commit.

## Dispatching an agent

In Claude Code, ask for the agent by name, for example "use the developer agent to build
slice X", or pick it with `/agents`. Give it one small task, the acceptance criteria and the
project name. The manager can dispatch the others (it has the Agent tool but no shell). Each role that
has a shell records its own handoff with the validated `append`. The manager has no shell, so a
manager-origin handoff is appended by the developer on the manager's instruction.

## Reading the handoff log

`workforce/status/handoffs.jsonl` is JSONL: one JSON object per line with `project`,
`from_role`, `to_role`, `summary`, `verdict` (`submitted`, `approved`, `rejected` or `blocked`)
and `ts` (UTC). Never edit it by hand. Policy lets all four roles write this one file; every other file under
`workforce/status/` is manager-only. Whoever commits a log line uses the `Role:` trailer of the
role that did the work. Write only through the validated `append` in
`tools/handoff_log.py`, and read it with `read_all`:

```
python -c "from tools.handoff_log import read_all; from pathlib import Path; [print(h) for h in read_all(Path('workforce/status/handoffs.jsonl'))]"
```

Tester sign-off rule: `append` refuses a deployer `submitted` handoff for a project unless the
log already holds a tester `approved` entry for that project. The deployer agent also checks this
before shipping.

## Approval gates (the director's explicit yes)

- The first push to GitHub (remote `https://github.com/n124j/ai-workforce.git`; not configured yet).
- Creating any public repository.
- Any cloud spend.
- Any publication, including running the Pages workflow (`.github/workflows/pages.yml`, manual dispatch only).
- Site copy approval before it is published.

An agent that needs one of these records a `blocked` handoff and stops.

## Employer rule

No current or past employer IP, data, names or metrics in any project, document, test or eval.
Use public or synthetic data only.

## Running the checks locally

```
python -m pytest -q
python -m tools.hygiene
python -m tools.role_paths --base <rev> --head HEAD
cd site && npm ci && npm test && npm run build
```

`tools.hygiene` and `tools.role_paths` print nothing and exit 0 when clean.

## Known limits

- Role rules are enforced by commit trailers and CI path checks, not by tool permissions alone.
  The trailer is self-declared, so an agent could declare the wrong role; the path check only
  catches a mismatch between the declared role and the files.
- The manager role may edit `workforce/policy.toml` and `.claude/agents/**`, so any change there
  needs the director's review.
- `from_role` in a handoff is self-declared and `append` cannot tell who actually wrote it, so
  the developer can write an entry as the manager, and a tester sign-off is only as trustworthy
  as the process around it.
- Sign-off via `read_all` does not prove a tester approval is newer than the latest developer
  change.
- Before the first Pages run, the director must set the repository's Pages source to "GitHub
  Actions", and may restrict the `github-pages` environment to the main branch and add required
  reviewers.
- The CI workflow (`.github/workflows/ci.yml`) has not yet run on GitHub.
