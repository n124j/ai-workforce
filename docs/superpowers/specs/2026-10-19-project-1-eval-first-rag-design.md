# Project 1: Eval-First Agentic RAG — Design

Date: 2026-10-19
Parent: `2026-10-19-ai-workforce-portfolio-design.md` (section 5, project 1). Constraints there (free and local, no employer IP, honest numbers, no paid keys) apply here unchanged.
Status: DRAFT. Every item marked **(my call)** is a designer's decision awaiting Niraj's confirmation.

## 1. Intent

Show, in one runnable repo, that Niraj treats AI quality as something you measure and gate, not something you hope for. A visitor clones it, runs one command, and sees a RAG system answer questions with citations, then sees an evaluation report with real numbers, and sees CI fail when a change makes the system worse.

The eval harness is the main deliverable. The RAG system exists to be measured. The harness is built as a reusable package so projects 2-5 can import it.

## 2. Goals, non-goals, anti-goals

Goals
- Hybrid retrieval (keyword + vector) with rank fusion and optional reranking.
- An answer step that must cite retrieved passages.
- An evaluation harness measuring retrieval quality, citation validity, answer faithfulness, latency, and token/cost use.
- A regression gate in CI that fails the build when deterministic metrics fall below a committed baseline.
- Published results that name the model, hardware, and date.

Non-goals
- No agent loops or tool use in this project (project 2 covers orchestration). "Agentic" here means a small retrieve -> answer -> verify-citations step, not an open-ended agent. **(my call)**
- No web UI beyond a minimal API and CLI. No auth, no multi-tenant, no cloud deploy.
- No attempt to beat frontier-model accuracy.

Anti-goals
- Hand-picked eval questions that flatter the system. The question set must include hard and unanswerable cases, and the report must show failures.
- A CI gate that is flaky because it calls a non-deterministic model.
- Any number in a README that a fresh clone cannot reproduce or that does not name its model.

## 3. Decisions (all my calls unless marked)

**Repo and name.** Own repo `eval-first-rag`, created later with Niraj's approval; local folder `C:\Users\newro\Documents\codes\claude\eval-first-rag`. Python package `evalrag`. Built by the workforce under the same role rules and commit trailers as `ai-workforce`.

**Corpus.** A pinned snapshot of a subset of the official Python 3.12 standard-library documentation (about 40 modules), under the PSF documentation license, stored as plain text chunks with source URL and version. Chosen because it is public, permissively licensed, technical enough to need real retrieval, unrelated to any employer, and familiar to Niraj's Python background.

**Question set (the "golden set").** About 60 questions, written with expected source passages: roughly 40 answerable from one passage, 10 needing two passages, 10 deliberately unanswerable from the corpus (the system should decline). Drafted by the workforce, reviewed by Niraj before it is frozen. Stored in the repo as JSONL with a version.

**Retrieval.** SQLite FTS5 for keyword search plus dense vectors from the nomic-embed-text-v1.5 model already installed in LM Studio, held as a NumPy matrix persisted on disk; fusion by reciprocal rank fusion. Optional cross-encoder reranker behind a flag, off in CI. Dependency-light on purpose: no vector database server.

**Answering.** Any OpenAI-compatible endpoint, configured by `.env` (`LLM_BASE_URL`, `LLM_MODEL`). Local default is LM Studio's server on `localhost:1234`. The prompt requires inline citations by chunk id; a post-check verifies each cited id exists and its quoted span appears in the chunk. Unanswerable questions should produce a fixed "not found in the provided documents" answer.

**Models.**
- CI and one-command demo: the small model already installed (Llama-3.2-1B-Instruct Q8) or recorded responses, see CI below.
- Published local numbers: a 7-8B instruct model at 4-bit that fits the 8 GB GPU through LM Studio's Vulkan backend. Needs a download of roughly 5 GB, which Niraj must approve; model choice is made after measuring what actually runs on his machine.

**Metrics.**
- Deterministic (no LLM): recall@k and MRR against expected source passages; citation validity rate; correct-refusal rate on unanswerable questions; latency percentiles; tokens in/out and tokens per second; cost reported as $0 for local with the token counts alongside.
- LLM-judged (local only, labeled noisy): faithfulness and answer relevance, scored by a judge model with a written rubric; reported with the judge model named. Never used by the CI gate.

**CI gate.** GitHub Actions runs only deterministic checks, on recorded model responses (a committed cache keyed by prompt hash) so the run needs no model and no GPU. The gate compares metrics with `baseline.json`; a drop beyond a stated tolerance fails the build. Changing the baseline requires a visible diff and a recorded reason. A `refresh-recordings` command regenerates recorded responses locally.

**Interfaces.** CLI (`evalrag ingest`, `ask`, `eval`, `report`) and a minimal FastAPI `/ask` endpoint. `docker compose up` starts the API and an optional Ollama service (compose profile); using a host LM Studio or an API key via `.env` is the documented alternative. Docker on Windows cannot use the AMD GPU, so the container path runs on CPU with a tiny model.

**Stack.** Python 3.12, pytest, ruff, FastAPI, NumPy, SQLite (stdlib). No heavyweight RAG framework: the pipeline is small, explicit, and readable, which is the point for a portfolio.

**Reusable harness.** `evalrag.evals` has no dependency on the retrieval code; it takes a callable that returns answers and sources, so projects 2-5 can evaluate themselves with it.

## 4. Deliverables

README with architecture diagram, how to run, results table (model, hardware, date), known limitations; decision records (why hybrid, why no framework, why recorded responses in CI); the frozen golden set; `baseline.json`; the published eval report; CI workflow; compose file.

## 5. Left to the builder

Chunking size and overlap (tune against the golden set, record the choice); fusion constant; prompt wording; exact tolerance values for the gate (must be justified from observed run-to-run variance); module layout; reranker choice.

## 6. Open items for Niraj

1. Confirm the corpus (Python 3.12 stdlib docs subset) or pick another.
2. Approve the roughly 5 GB 7-8B model download later, when benchmarking begins.
3. Confirm the repo name and local folder, and that the repo is created and pushed only with his approval.
4. He reviews the golden question set before it is frozen.
