# AI Workforce Portfolio — Design

Date: 2026-10-19
Owner / director: Niraj Byanjankar (Principal Software Engineer, 10+ years, GenAI / agentic / AI platform, GCP-certified)
Source of truth for his background: his résumé (not copied into this repo).

## 1. Intent

Niraj wants a public portfolio that makes a recruiter or hiring manager conclude, within a few minutes, that he is sharp, fluent in AI, and has done his homework in his specialization. The portfolio is built by an "AI workforce": a small team of Claude Code subagents (manager, developer, tester, deployer) that Niraj directs.

Why: his résumé lists strong claims (RAG, multi-agent orchestration, evals, HITL, responsible AI, platform engineering) but his employer's work is proprietary. Public, original projects let him demonstrate the same depth on his own terms.

What "success" looks like:
- Each project shows depth, not existence: evals, failure handling, cost/latency numbers, guardrails, and written tradeoffs.
- A visitor can clone any project and run it with one `docker compose up`, without paying for or owning an API key.
- The workforce itself is a credible demonstration of his "AI-assisted engineering" claim.

## 2. Goals, non-goals, anti-goals

Goals
- Five original projects (section 5) plus a small portfolio site tying them together.
- A reusable workforce (agent definitions, process, quality gates) that is itself documented as part of the portfolio.
- Honest, reproducible results (eval numbers, benchmarks) published with each project.

Non-goals
- No paid cloud resources. No live GCP deployment (decision below).
- No more than five projects. Breadth is not the point.
- No generic tutorial clones.

Anti-goals (would make this a failure even if it technically works)
- Any current or past employer IP, data, code, internal names, or metrics. Projects are original builds on public or synthetic data that echo problems he has solved.
- Inflated or fabricated claims, benchmark numbers, or usage stats.
- Secrets, tokens, or personal data committed to any repo.
- Projects that only run on the author's machine or need a paid key.

## 3. Constraints and decisions (Niraj's calls)

- **Free and local only for now:** Docker for packaging, GitHub Actions for CI, GitHub Pages for the portfolio site.
- **Local models by default** (Ollama / LM Studio are already installed on his machine). Paid providers (OpenAI, Gemini, Claude) are opt-in via the user's own keys in a local `.env`, never committed. Eval numbers on local models will be lower than on frontier models; reports state which model produced them.
- **Terraform for the GCP project (project 4):** written and validated (`terraform validate`/`plan` offline only), never applied. The README says so plainly.
- **Repo location:** `C:\Users\newro\Documents\codes\claude\ai-workforce` (git repo, later the GitHub repo). Separate from `taiq-platform`.
- **Approvals needed from Niraj:** first push to GitHub, creating any public repo, any cloud spend, and any outward-facing publication. GitHub access comes through his existing login (e.g. `gh auth`), never a token pasted into chat.
- **Role change:** the original ask (4 developers, 1 manager, 1 director) became 1 developer, 1 tester, 1 manager, 1 deployer. Niraj acts as director.

## 4. The workforce

Implemented as Claude Code subagents, defined in `.claude/agents/` in the workforce repo, each with its own instructions and tool limits.

| Role | Responsibility | Hard rule |
|---|---|---|
| Manager | Turns each project into a spec, acceptance criteria and backlog; assigns tasks; checks each handoff against criteria; keeps a status log; escalates to Niraj | Writes no product code |
| Developer | Builds in small increments, test-first; writes README and decision records (ADRs) as it goes | Cannot mark its own work done |
| Tester | Writes independent tests, evals and adversarial cases; reviews developer code against acceptance criteria | Cannot edit product source; files defects to the manager |
| Deployer | Owns Dockerfiles, compose files, GitHub Actions, Pages publishing, Terraform validation, releases | Deploys/publishes only after tester sign-off and, for anything public, Niraj's approval |

Per-project loop: manager writes spec + acceptance criteria -> developer builds a slice -> tester verifies -> manager gates -> repeat -> deployer ships. Every project ends with: README, architecture diagram, decision records, and published eval/benchmark results.

Orchestration mechanism (builder's call): Claude Code's Agent tool dispatching these subagents from a manager-driven session, using the superpowers workflows (writing-plans, subagent-driven-development, TDD, verification-before-completion) already installed.

## 5. The projects

All are original, run via `docker compose up`, default to local models, and use public or synthetic data.

1. **Eval-first agentic RAG.** Hybrid retrieval (keyword + vector) with reranking over a public corpus; an evaluation harness scoring faithfulness, retrieval quality, cost, and latency; evals run as a CI gate so a regression fails the build. The harness is reusable by the other projects.
2. **Multi-agent orchestrator with human-in-the-loop.** A supervisor coordinates specialist agents on a realistic ops problem (e.g. triaging simulated data-pipeline incidents). Durable state, confidence-based escalation to a human, approval gates, full audit trail.
3. **Claude Code engineering agents.** Open-source agents plus an MCP server automating code review, deployment validation, and doc generation, packaged as a GitHub Action. The workforce itself is a case study.
4. **LLM metadata enrichment and governance (GCP-style).** Pipeline that classifies and enriches data-catalog metadata with an LLM, with PII detection and GDPR/CCPA-style guardrails, on synthetic data. Built to run locally (e.g. DuckDB or Postgres standing in for BigQuery, a local scheduler in place of Composer) with a Terraform module showing the GCP target, validated but not applied.
5. **LLM gateway with observability and guardrails.** Proxy in front of multiple providers (local models by default, optional OpenAI/Gemini/Claude) with routing, caching, cost tracking, guardrails, and Prometheus/Grafana dashboards.

Plus: **portfolio site** (GitHub Pages) with an overview, per-project case studies, architecture diagrams, and the decisions behind each.

Suggested order (my call): shared repo standards and CI scaffolding -> project 1 -> 5 -> 2 -> 4 -> 3, with the site growing alongside. Niraj can reorder.

## 6. Quality bar (applies to every project)

- Test-first; tests and evals run in CI on GitHub Actions.
- Reproducible: pinned dependencies, one-command run, documented hardware needs for local models.
- Each README states: the problem, architecture diagram, how to run, what was measured, on which model, and known limitations.
- Decision records explain tradeoffs and what was rejected.
- Security hygiene: no secrets in git, `.env.example` only, dependency and secret scanning in CI.

## 7. Left to the builder

- Languages and frameworks per project (default leaning: Python backend, TypeScript/React where a UI is needed, matching his résumé), as long as each runs via Docker.
- Choice of specific local models, vector store, and corpus for project 1, within the free/local constraint.
- Site framework for GitHub Pages.
- Exact agent prompts and tool permissions for the four subagents.
- Repo structure: monorepo with one folder per project vs. one repo per project (the builder should recommend one; separate public repos need Niraj's approval).

## 8. Calls made by the designer (not yet confirmed by Niraj)

- **CI evals:** free GitHub runners have no GPU and about 7 GB RAM, so CI runs a small fixed golden set against a tiny CPU model or recorded/cached responses (deterministic gate). Heavier evals run locally and their results are published with the model named. Reports never mix the two.
- **Docker and local models:** each compose stack includes an optional Ollama service (compose profile) so a visitor needs no host install; pointing at a host Ollama or an API key via `.env` is the documented alternative. READMEs state first-run model download size and time.
- **Workforce enforcement:** roles are enforced, not just described: per-agent tool allowlists in the agent definitions, CI path checks (e.g. tester changes cannot touch product source), and a status log plus handoff trail kept in the repo as visible evidence.
- **Employer-IP line:** all data is synthetic or public; no real names, internal system names, or metrics from his employers. Niraj reviews each project's spec against this rule before build starts.
- **Site copy:** Niraj approves all published copy. The site scaffold is built early; case-study text is written after real measured results exist.

## 9. Answers from Niraj and what they imply

**Hardware (from his System > About screenshot):** AMD Ryzen 9 3900X (12 cores), 128 GB RAM, AMD Radeon RX 6600 XT with 8 GB VRAM, about 2.4 TB free disk, Windows 11.
- Implication (designer's reading): 8 GB VRAM fits 7-8B models at 4-bit quantization. The RX 6600 XT is an AMD card, and AMD GPU support in Ollama on Windows is patchy for this model; LM Studio's Vulkan backend is the more dependable route for GPU speed. If GPU acceleration fails, 128 GB RAM still allows CPU inference, just slower. The builder should verify what actually works on this machine before committing to a model list, and record tokens/second in the READMEs.
- Docker containers on Windows generally cannot use the AMD GPU, so Dockerized stacks should expect CPU inference or call a host model server. This reinforces the call in section 8 that CI and the one-command path use a tiny model.

**GitHub:** username `n124j`; workforce repo `https://github.com/n124j/ai-workforce.git`. Niraj gave one repo URL and did not pick between monorepo and separate repos.
- Designer's call, pending his confirmation: `ai-workforce` holds the workforce definitions, shared standards, and the portfolio hub site; each of the five projects gets its own public repo created later, each one only with his approval at that point. Nothing is pushed until he approves.

**Timeline:** the plan is vertical, not horizontal: ship a thin portfolio site plus project 1 first (the eval harness it produces is reused later), then add the remaining projects one at a time, publishing each when it meets the quality bar in section 6. Partial projects are not published; the site may list upcoming ones as "in progress" only if he approves that wording.
