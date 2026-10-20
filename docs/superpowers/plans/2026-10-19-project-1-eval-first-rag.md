# Project 1: Eval-First Agentic RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `eval-first-rag`: a hybrid-retrieval RAG system with cited answers, a reusable evaluation harness, and a CI gate that fails when deterministic quality metrics regress against a committed baseline.

**Architecture:** A small explicit Python package `evalrag` (no RAG framework). Keyword search (SQLite FTS5) and dense search (NumPy matrix of nomic-embed-text-v1.5 vectors) are fused with reciprocal rank fusion. Answers come from any OpenAI-compatible endpoint and must cite chunk ids, which a post-check verifies. The harness `evalrag.evals` knows nothing about retrieval: it scores any callable returning a `SutResult`. CI replays recorded embeddings and model responses (cache keyed by hash), so the gate needs no model and no GPU.

**Tech Stack:** Python 3.12, pytest, ruff, FastAPI, httpx, NumPy, SQLite (stdlib), Docker, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-19-project-1-eval-first-rag-design.md` (child of `2026-10-19-ai-workforce-portfolio-design.md`). Built by the same four-role workforce and conventions as `ai-workforce` (`docs/workforce.md` there).

## Global Constraints

- Free and local only; no paid keys required to run anything. Local default endpoint `http://localhost:1234/v1` (LM Studio); config via `.env` keys `LLM_BASE_URL`, `LLM_MODEL`, `EMBED_BASE_URL`, `EMBED_MODEL`; `.env.example` holds names only, values empty except the localhost URLs.
- No current or past employer IP, names, data or metrics anywhere.
- Corpus: a pinned subset (about 40 modules) of the official Python 3.12 standard-library documentation, PSF documentation license; each chunk carries source URL and docs version.
- Golden set: about 60 questions: 40 single-passage, 10 multi-passage, 10 unanswerable. Unanswerable answers must be the fixed text `Not found in the provided documents.`
- Citation format in answers: `[chunk_id: "exact quote"]`.
- Retrieval: SQLite FTS5 keyword search + dense vectors (`nomic-embed-text-v1.5`) as a persisted NumPy matrix; reciprocal rank fusion with constant `k=60`; no vector database server.
- Deterministic metrics (CI gate): recall@k, MRR, citation validity rate, correct-refusal rate, latency percentiles, token counts. LLM-judged faithfulness and relevance are local-only, labeled noisy, and never used by the gate.
- CI never calls a live model: a replay cache miss must fail with the missing key.
- Published numbers always name model, hardware and date. Nothing is pushed, published or made public, and no model or corpus is downloaded, without Niraj's explicit yes.
- Python 3.12, stdlib-only for anything not named in the stack; pin all dependencies exactly.
- Role ownership (checked by `python -m tools.role_paths`, commit ends with `Role: <role>` then `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`): developer `src/**`, `corpus/**`, `scripts/**`, `tests/unit/**`, `docs/adr/**`, `README.md`, `pyproject.toml`, `requirements*.txt`, `.gitignore`, `.env.example`, `LICENSE`, `tools/**`; tester `tests/acceptance/**`, `evals/**`; deployer `.github/**`, `docker/**`, `Dockerfile*`, `compose*.yaml`, `.gitleaks*`; manager `docs/superpowers/**`, `workforce/**` (except the handoff log, writable by all), `.claude/agents/**`.

## Review Focus

1. FTS5 queries containing quotes, operators (`AND`, `NEAR`, `*`), punctuation, or only whitespace: `KeywordIndex.search` must not raise and must return `[]` for an empty query.
2. Model answers that cite a chunk id that was not retrieved, quote text absent from the chunk, give no citation, or paraphrase the refusal: citation check fails closed; only the exact refusal text counts as a refusal.
3. A replay cache miss (changed prompt, new question): raises `ReplayMiss` naming the key; never falls through to a network call.
4. Golden set integrity: duplicate ids, expected sources missing from the corpus, an unanswerable item that lists expected sources, an answerable item that lists none: loader rejects each.
5. Gate with a metric missing from the result, NaN, or a baseline entry with the wrong direction: fails the gate; never passes silently.
6. Dense index with an embedding dimension that differs from the stored matrix, or an empty corpus: clear error, not a shape crash.

---

## File Structure

```
src/evalrag/
  models.py config.py chunking.py corpus.py
  retrieval/{keyword,embedder,dense,fusion,hybrid,rerank}.py
  generation/{llm,answer}.py
  pipeline.py cli.py api.py
  evals/{metrics,dataset,runner,gate,report,judge}.py   # no imports from retrieval/generation
scripts/fetch_corpus.py        corpus/ (text pages + manifest.json)
evals/{golden/golden.jsonl,baseline.json,recordings/,reports/}
tests/unit/  tests/acceptance/
Dockerfile compose.yaml docker/  .github/workflows/ci.yml  docs/adr/
tools/ (role_paths, handoff_log, hygiene copied from ai-workforce)  workforce/policy.toml  .claude/agents/
```

### Task 1: Bootstrap the repo with workforce standards

**Files:**
- Create (new git repo at `C:\Users\newro\Documents\codes\claude\eval-first-rag`, branch `master`): `pyproject.toml`, `requirements-dev.txt`, `.gitignore`, `.env.example`, `.gitattributes`, `LICENSE` (MIT, holder "Niraj Byanjankar"), `README.md` (stub), `src/evalrag/__init__.py`, `tools/` (copy `role_paths.py`, `handoff_log.py`, `hygiene.py`, `__init__.py` from `ai-workforce`), `workforce/policy.toml`, `.claude/agents/{manager,developer,tester,deployer}.md`, `.gitleaks.toml`, `.github/workflows/ci.yml` (python job only: install, `ruff check`, `pytest`, `tools.hygiene`, `tools.role_paths`), `tests/unit/test_smoke.py`
- Test: `tests/acceptance/test_repo_standards.py`

**Interfaces:**
- Produces: `evalrag.__version__: str = "0.1.0"`; the role/commit conventions every later task relies on.

- [ ] **Step 1: Write failing acceptance test** (tester): policy loads with the four roles; developer globs include `src/**`, `corpus/**`, `scripts/**`; tester globs include `evals/**`; `.env.example` has `LLM_BASE_URL` and `EMBED_MODEL`; `tools.hygiene.check_repo` returns `[]`; `import evalrag; evalrag.__version__ == "0.1.0"`.
- [ ] **Step 2: Run** `python -m pytest tests/acceptance -v`. Expected: FAIL.
- [ ] **Step 3: Create the repo and files.** Copy tools and agent files verbatim from `ai-workforce`; adapt `workforce/policy.toml` to the ownership in Global Constraints (drop `site/**` entries; keep `workforce/status/handoffs.jsonl` writable by all four roles); update the globs listed inside each agent file to match the policy. Pin ruff, pytest, PyYAML exactly in `requirements-dev.txt`.
- [ ] **Step 4: Run** `python -m pytest -q`, `python -m ruff check .`, `python -m tools.hygiene`. Expected: all clean.
- [ ] **Step 5: Commit in role order** (tester test first, then manager policy/agents, then developer files, then deployer CI/gitleaks), each with the correct trailer. Do not add a remote.

### Task 2: Domain models, config, chunking

**Files:**
- Create: `src/evalrag/models.py`, `src/evalrag/config.py`, `src/evalrag/chunking.py`
- Test: `tests/unit/test_chunking.py`, `tests/unit/test_config.py`

**Interfaces:**
- Produces: `@dataclass(frozen=True) Document(doc_id: str, title: str, url: str, version: str, text: str)`; `Chunk(chunk_id: str, doc_id: str, ordinal: int, text: str, url: str)` with `chunk_id == f"{doc_id}#{ordinal:03d}"`; `Hit(chunk_id: str, score: float, rank: int)`; `Settings` with `llm_base_url, llm_model, embed_base_url, embed_model, data_dir, top_k` and `Settings.from_env(env: Mapping[str, str]) -> Settings` (raises `ConfigError` naming the missing key); `chunk_document(doc: Document, size: int, overlap: int) -> list[Chunk]` (word-based windows, `0 <= overlap < size`).

- [ ] **Step 1: Failing tests:** `test_chunk_ids_are_stable_and_ordered`; `test_overlap_repeats_exact_words` (`size=5, overlap=2` over ten words gives 3 chunks sharing 2 words each); `test_empty_text_yields_no_chunks`; `test_invalid_overlap_raises_ValueError` (`overlap >= size`); `test_from_env_reports_missing_key`.
- [ ] **Step 2: Run** `python -m pytest tests/unit/test_chunking.py tests/unit/test_config.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the signatures above in the named files.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Commit** (developer).

### Task 3: Corpus snapshot and loader

**Files:**
- Create: `scripts/fetch_corpus.py`, `corpus/manifest.json`, `corpus/*.txt` (about 40 module pages), `src/evalrag/corpus.py`
- Test: `tests/unit/test_corpus.py`

**Interfaces:**
- Produces: `load_corpus(corpus_dir: Path) -> list[Document]` (reads `manifest.json`: list of `{doc_id, title, url, version, file, sha256}`; verifies each file's sha256, raises `CorpusError` on mismatch or a missing file); `scripts/fetch_corpus.py --out corpus --version 3.12` downloads the official Python 3.12 text-docs archive over HTTPS, extracts a fixed list of about 40 stdlib module pages (list lives in the script), writes files and the manifest with sha256s.

- [ ] **Step 1: Failing tests** (use a tmp corpus): `test_load_corpus_roundtrip`; `test_hash_mismatch_raises`; `test_missing_file_raises`; `test_manifest_requires_all_fields`.
- [ ] **Step 2: Run** `python -m pytest tests/unit/test_corpus.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `load_corpus` and the fetch script.
- [ ] **Step 4: Run** the tests. Expected: PASS.
- [ ] **Step 5: Approval gate.** The fetch script downloads a file from the internet. Ask Niraj for an explicit yes naming the source URL and approximate size before running it. After the yes, run it once, commit `corpus/**` (developer), and record the archive URL and sha256 in `docs/adr/0001-corpus.md`.
- [ ] **Step 6: Commit** (developer).

### Task 4: Keyword index (FTS5)

**Files:**
- Create: `src/evalrag/retrieval/__init__.py`, `src/evalrag/retrieval/keyword.py`
- Test: `tests/unit/test_keyword.py`

**Interfaces:**
- Consumes: `Chunk`, `Hit`.
- Produces: `KeywordIndex(db_path: Path)` with `add(chunks: list[Chunk]) -> None`, `search(query: str, k: int) -> list[Hit]` (BM25 via FTS5 `bm25()`, best first, rank starting at 1), `count() -> int`, `close()`. Queries are sanitized to plain word tokens before reaching FTS5.

- [ ] **Step 1: Failing tests:** `test_finds_exact_term`; `test_ranks_more_relevant_chunk_first`; `test_special_characters_do_not_raise` (`'"unterminated'`, `"a AND OR NEAR(*"`, `"foo*bar"`); `test_empty_and_whitespace_query_return_empty`; `test_k_limits_results`; `test_persists_to_disk` (reopen the db).
- [ ] **Step 2: Run** `python -m pytest tests/unit/test_keyword.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `KeywordIndex` (table `chunks_fts` with `chunk_id UNINDEXED, text`).
- [ ] **Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** (developer).

### Task 5: Embedders, record/replay, dense index

**Files:**
- Create: `src/evalrag/retrieval/embedder.py`, `src/evalrag/retrieval/dense.py`
- Test: `tests/unit/test_embedder.py`, `tests/unit/test_dense.py`

**Interfaces:**
- Produces in `embedder.py`: `class Embedder(Protocol): def embed(self, texts: list[str]) -> np.ndarray` (float32, shape `(n, dim)`); `OpenAICompatEmbedder(base_url: str, model: str, client: httpx.Client | None = None)` (POST `{base_url}/embeddings`, batches of 32); `RecordingEmbedder(inner: Embedder, cache_path: Path)` (saves text-sha256 -> float16 vector to an `.npz` on `flush()`); `ReplayEmbedder(cache_path: Path)` (raises `ReplayMiss(key)` for unseen text); `ReplayMiss(KeyError)`.
- Produces in `dense.py`: `DenseIndex()` with `add(chunk_ids: list[str], vectors: np.ndarray) -> None`, `search(vector: np.ndarray, k: int) -> list[Hit]` (cosine, best first), `save(path: Path)`, `load(path: Path) -> DenseIndex`; raises `DimensionMismatch` when dimensions differ and `EmptyIndex` when searching an empty index.

- [ ] **Step 1: Failing tests:** embedder with an `httpx.MockTransport`: `test_openai_compat_posts_and_parses`, `test_batches_over_32`; `test_recording_then_replay_roundtrip`; `test_replay_miss_names_key_and_never_calls_inner`; dense: `test_cosine_order`, `test_save_load_roundtrip`, `test_dimension_mismatch_raises`, `test_empty_index_search_raises`, `test_k_larger_than_corpus_returns_all`.
- [ ] **Step 2: Run** `python -m pytest tests/unit/test_embedder.py tests/unit/test_dense.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** both modules; add `numpy` and `httpx` pinned in `pyproject.toml` runtime dependencies.
- [ ] **Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** (developer).

### Task 6: Fusion, hybrid retriever, reranker hook

**Files:**
- Create: `src/evalrag/retrieval/fusion.py`, `src/evalrag/retrieval/hybrid.py`, `src/evalrag/retrieval/rerank.py`
- Test: `tests/unit/test_fusion.py`, `tests/unit/test_hybrid.py`

**Interfaces:**
- Consumes: `KeywordIndex`, `DenseIndex`, `Embedder`, `Hit`.
- Produces: `rrf(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]` (score = sum of `1/(k + rank)`, rank 1-based, sorted descending, ties broken by chunk id for determinism); `class Reranker(Protocol): def rerank(self, query: str, hits: list[Hit], texts: dict[str, str]) -> list[Hit]`; `NoopReranker`; `CrossEncoderReranker(model_name: str)` (lazy-imports `sentence_transformers` inside `__init__`; raises `RerankerUnavailable` with an install hint when absent; not installed by default); `HybridRetriever(keyword, dense, embedder, reranker=None)` with `retrieve(query: str, k: int) -> list[Hit]` returning fused hits, ranks renumbered from 1.

- [ ] **Step 1: Failing tests:** `test_rrf_known_values` (two rankings, exact expected scores with `k=60`); `test_rrf_tie_break_is_deterministic`; `test_item_in_both_lists_beats_item_in_one`; hybrid with fake indexes: `test_hybrid_merges_keyword_and_dense`; `test_hybrid_with_empty_keyword_result_uses_dense`; `test_reranker_reorders_but_keeps_membership`; `test_cross_encoder_unavailable_raises_clear_error` (when the module is absent).
- [ ] **Step 2: Run** `python -m pytest tests/unit/test_fusion.py tests/unit/test_hybrid.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** (developer).

### Task 7: LLM client with record/replay

**Files:**
- Create: `src/evalrag/generation/__init__.py`, `src/evalrag/generation/llm.py`
- Test: `tests/unit/test_llm.py`

**Interfaces:**
- Produces: `@dataclass(frozen=True) Completion(text: str, prompt_tokens: int, completion_tokens: int, latency_s: float)`; `class LLMClient(Protocol): def complete(self, messages: list[dict[str, str]]) -> Completion`; `OpenAICompatClient(base_url, model, client=None, temperature: float = 0.0, max_tokens: int = 512)`; `request_key(model: str, messages, temperature: float, max_tokens: int) -> str` (sha256 of canonical JSON, keys sorted); `RecordingClient(inner, cache_path: Path)` (writes one JSON object per key, stable ordering); `ReplayClient(cache_path: Path)` (raises `ReplayMiss(key)`; replayed `latency_s` is the recorded value).

- [ ] **Step 1: Failing tests** (httpx mock transport): `test_parses_text_and_usage`; `test_request_key_is_order_insensitive_for_dict_keys`; `test_record_then_replay_returns_identical_completion`; `test_replay_miss_never_calls_inner`; `test_http_error_raises_LLMError_with_status`.
- [ ] **Step 2: Run** `python -m pytest tests/unit/test_llm.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** (developer).

### Task 8: Answering with verified citations

**Files:**
- Create: `src/evalrag/generation/answer.py`, `src/evalrag/pipeline.py`
- Test: `tests/unit/test_answer.py`, `tests/unit/test_pipeline.py`

**Interfaces:**
- Consumes: `LLMClient`, `HybridRetriever`, `Chunk`.
- Produces: `REFUSAL_TEXT = "Not found in the provided documents."`; `build_messages(question: str, chunks: list[Chunk]) -> list[dict[str, str]]` (system prompt requires `[chunk_id: "exact quote"]` citations and the refusal text when the context lacks the answer); `parse_citations(text: str) -> list[Citation]` with `Citation(chunk_id: str, quote: str)`; `verify_citations(citations, chunks: list[Chunk]) -> CitationReport(valid: bool, unknown_ids: list[str], missing_quotes: list[str])` (valid only if at least one citation exists, every id is among `chunks`, and every quote is a case-sensitive substring of its chunk); `is_refusal(text: str) -> bool` (stripped text equals `REFUSAL_TEXT` exactly); `RagPipeline(retriever, llm, chunks_by_id: dict[str, Chunk], k: int)` with `ask(question: str) -> Answer` where `Answer(text, citations, report, retrieved_ids, refused, completion)`.

- [ ] **Step 1: Failing tests:** `test_parse_citations_handles_multiple_and_ignores_malformed`; `test_verify_rejects_unknown_chunk_id`; `test_verify_rejects_quote_not_in_chunk`; `test_verify_requires_at_least_one_citation`; `test_refusal_must_match_exactly` (variants with extra words fail); `test_pipeline_ask_wires_retrieval_prompt_and_verification` (fake retriever and LLM); `test_refusal_answer_marks_refused_and_skips_citation_requirement`.
- [ ] **Step 2: Run** `python -m pytest tests/unit/test_answer.py tests/unit/test_pipeline.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement.** A refusal answer is `refused=True` and its `report.valid` is not required.
- [ ] **Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** (developer).

### Task 9: Eval harness core (independent of retrieval)

**Files:**
- Create: `src/evalrag/evals/__init__.py`, `src/evalrag/evals/metrics.py`, `src/evalrag/evals/dataset.py`, `src/evalrag/evals/runner.py`
- Test: `tests/unit/test_metrics.py`, `tests/unit/test_dataset.py`, `tests/unit/test_runner.py`, plus `tests/acceptance/test_harness_independence.py`

**Interfaces:**
- Produces: `recall_at_k(expected: set[str], retrieved: list[str], k: int) -> float` (an empty `expected` raises `ValueError`); `mrr(expected: set[str], retrieved: list[str]) -> float` (reciprocal rank of the first hit, 0.0 if none); `percentile(values: list[float], p: float) -> float` (nearest-rank); `GoldenItem(id, question, expected_sources: tuple[str, ...], answerable: bool, kind: str)` with `kind` in `single|multi|unanswerable`; `load_golden(path: Path, known_sources: set[str] | None = None) -> list[GoldenItem]` enforcing Review Focus 4; `SutResult(answer: str, retrieved_ids: list[str], cited_ids: list[str], citation_ok: bool, refused: bool, latency_s: float, prompt_tokens: int, completion_tokens: int)`; `SystemUnderTest = Callable[[str], SutResult]`; `run_eval(sut: SystemUnderTest, items: list[GoldenItem], k: int = 5) -> EvalResult` with per-item rows and `EvalResult.metrics: dict[str, float]` containing exactly `recall_at_k`, `mrr`, `citation_validity_rate`, `correct_refusal_rate`, `latency_p50_s`, `latency_p95_s`, `prompt_tokens_total`, `completion_tokens_total`. `recall_at_k` and `mrr` average over answerable items only; `citation_validity_rate` over answerable non-refused items; `correct_refusal_rate` over unanswerable items (refused counts as correct); an answerable item that is refused counts as a miss for citation validity.

- [ ] **Step 1: Failing tests:** metrics with exact values (`recall_at_k({"a","b"}, ["a","x","b"], 2) == 0.5`, `mrr({"b"}, ["a","b"]) == 0.5`, nearest-rank percentile on `[1,2,3,4]`); `test_recall_empty_expected_raises`; dataset: one test per Review Focus 4 case; runner with a scripted fake SUT: aggregates match hand-computed values, an unanswerable item answered (not refused) counts as incorrect. Acceptance (tester): `test_evals_package_imports_nothing_from_retrieval_or_generation` (scan the AST of every file under `src/evalrag/evals/` for imports of `evalrag.retrieval`, `evalrag.generation`, `evalrag.pipeline`).
- [ ] **Step 2: Run** `python -m pytest tests/unit/test_metrics.py tests/unit/test_dataset.py tests/unit/test_runner.py tests/acceptance/test_harness_independence.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** (tester for the acceptance test, committed first; developer for src and unit tests).

### Task 10: Baseline gate, report, optional judge

**Files:**
- Create: `src/evalrag/evals/gate.py`, `src/evalrag/evals/report.py`, `src/evalrag/evals/judge.py`
- Test: `tests/unit/test_gate.py`, `tests/unit/test_report.py`, `tests/unit/test_judge.py`

**Interfaces:**
- Produces in `gate.py`: baseline JSON shape `{"model": str, "date": str, "reason": str, "metrics": {name: {"value": float, "tolerance": float, "direction": "higher"|"lower"}}}`; `load_baseline(path: Path) -> Baseline` (validates shape; unknown direction raises `BaselineError`); `compare(metrics: dict[str, float], baseline: Baseline) -> list[Regression]` (`Regression(name, baseline, actual, tolerance)`; a metric regresses when it is worse than `value` by more than `tolerance` in its direction; a metric missing from `metrics`, NaN, or infinite is a regression); `gate(metrics, baseline_path) -> int` returns 0 or 1.
- Produces in `report.py`: `render_markdown(result: EvalResult, meta: dict[str, str]) -> str` (table of metrics, then the per-item failures: every answerable item with recall 0 or invalid citation and every unanswerable item answered; `meta` must contain `model`, `hardware`, `date`, else `ValueError`).
- Produces in `judge.py`: `JudgeScore(faithfulness: int, relevance: int, rationale: str)` (1-5); `judge_answer(llm: LLMClient, question: str, answer: str, context: list[str]) -> JudgeScore` (prompt with a written rubric, parses JSON, raises `JudgeError` on malformed output); results are labeled `noisy` in reports and never read by `gate`.

- [ ] **Step 1: Failing tests:** `test_within_tolerance_passes`; `test_worse_than_tolerance_fails_for_higher_is_better`; `test_lower_is_better_direction_for_latency`; `test_missing_nan_inf_metrics_fail` (Review Focus 5); `test_bad_direction_rejected`; `test_report_lists_failures_and_requires_meta`; `test_judge_parses_valid_json_and_rejects_garbage`; `test_gate_module_does_not_import_judge`.
- [ ] **Step 2: Run** `python -m pytest tests/unit/test_gate.py tests/unit/test_report.py tests/unit/test_judge.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** (developer).

### Task 11: CLI and API

**Files:**
- Create: `src/evalrag/cli.py`, `src/evalrag/api.py`, `src/evalrag/__main__.py`
- Test: `tests/unit/test_cli.py`, `tests/unit/test_api.py`

**Interfaces:**
- Consumes: everything above.
- Produces: console command `evalrag` with subcommands `ingest` (`--corpus corpus --data-dir data [--record-embeddings PATH | --replay-embeddings PATH]`: chunk, build FTS5 and dense indexes), `ask QUESTION`, `eval` (`--golden PATH --report-out PATH [--replay-llm PATH | --record-llm PATH] [--replay-embeddings PATH]`; writes metrics JSON and a Markdown report), `gate` (`--metrics PATH --baseline PATH`, exit 1 on regression), `refresh-recordings` (re-runs `ingest` and `eval` against live endpoints in recording mode). `main(argv: list[str] | None = None) -> int`. FastAPI app factory `create_app(pipeline: RagPipeline) -> FastAPI` with `GET /health` and `POST /ask` (`{"question": str}` -> `{"answer": str, "citations": [...], "refused": bool}`; empty question -> 422).

- [ ] **Step 1: Failing tests:** CLI with fake components injected through a factory: `test_gate_exit_codes_zero_and_one`; `test_eval_in_replay_mode_never_opens_a_network_connection` (monkeypatch `socket.socket` to raise); `test_ingest_then_ask_roundtrip_on_tiny_corpus`; API with `fastapi.testclient`: `test_health`, `test_ask_returns_citations`, `test_empty_question_is_422`.
- [ ] **Step 2: Run** `python -m pytest tests/unit/test_cli.py tests/unit/test_api.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement.** Add `fastapi` and `uvicorn` pinned to `pyproject.toml`; `[project.scripts] evalrag = "evalrag.cli:main"`.
- [ ] **Step 4: Run** the tests, then `python -m ruff check .` and the full suite. Expected: PASS.
- [ ] **Step 5: Commit** (developer).

### Task 12: Golden set, recordings, frozen baseline

**Files:**
- Create: `evals/golden/golden.jsonl`, `evals/golden/README.md`, `evals/recordings/embeddings.npz`, `evals/recordings/llm.jsonl`, `evals/baseline.json`, `evals/reports/local-small-model.md`
- Test: `tests/acceptance/test_golden_set.py`, `tests/acceptance/test_eval_gate_end_to_end.py`

**Interfaces:**
- Consumes: `load_golden`, `load_corpus`, the CLI.
- Produces: the frozen golden set (about 60 items: 40 `single`, 10 `multi`, 10 `unanswerable`), recordings from a real run with the installed small model (Llama-3.2-1B-Instruct Q8 and nomic-embed-text-v1.5 via LM Studio), `baseline.json` with tolerances justified from repeated live runs' variance, and the first report naming model, hardware (AMD Ryzen 9 3900X, RX 6600 XT 8 GB, 128 GB RAM) and date.

- [ ] **Step 1: Failing acceptance tests** (tester): `test_golden_counts_and_kinds` (40/10/10 within +-2, ids unique); `test_every_expected_source_exists_in_corpus`; `test_unanswerable_items_have_no_expected_sources`; `test_baseline_has_all_required_metrics_with_directions`; `test_end_to_end_replay_eval_passes_gate` (run `evalrag eval` in replay mode over the committed recordings, then `evalrag gate`; exit 0); `test_end_to_end_gate_fails_on_degraded_metrics` (copy the metrics, lower `recall_at_k` beyond tolerance, expect exit 1).
- [ ] **Step 2: Run** `python -m pytest tests/acceptance -v`. Expected: FAIL (files missing).
- [ ] **Step 3: Draft the golden set** (tester role): write questions with expected source ids from the committed corpus; include hard cases (synonyms, questions whose answer spans two modules, near-miss unanswerable questions about real stdlib features not in the subset).
- [ ] **Step 4: Review gate, do not skip.** Show Niraj the golden set (counts, ten sample questions, all ten unanswerable ones) and wait for his explicit yes or edits before freezing. Do not record against an unreviewed set.
- [ ] **Step 5: Record.** With LM Studio serving the two installed models, run `evalrag refresh-recordings`, run the eval three times live to measure variance, write `baseline.json` (values from the replay run; each tolerance at least the observed spread, with the reasoning in the `reason` field), and generate the first report.
- [ ] **Step 6: Run** `python -m pytest tests/acceptance -v`. Expected: PASS.
- [ ] **Step 7: Commit** (tester; each commit message states what was recorded and with which model).

### Task 13: CI gate and Docker

**Files:**
- Modify: `.github/workflows/ci.yml` (add the eval-gate steps)
- Create: `Dockerfile`, `compose.yaml`, `docker/README.md`
- Test: `tests/acceptance/test_ci_and_docker.py`

**Interfaces:**
- Produces: CI steps after `pytest`: `python -m evalrag eval --golden evals/golden/golden.jsonl --replay-llm evals/recordings/llm.jsonl --replay-embeddings evals/recordings/embeddings.npz --report-out evals/reports/ci.md` then `python -m evalrag gate --metrics <out> --baseline evals/baseline.json`; uploads the report as a workflow artifact; every third-party action SHA-pinned; `permissions: contents: read`. `Dockerfile`: Python 3.12 slim, non-root user, installs the package, `CMD ["uvicorn", "evalrag.api:app", ...]`. `compose.yaml`: service `api` on port 8000 reading `.env`; service `ollama` under `profiles: ["ollama"]`; `LLM_BASE_URL` documented for host LM Studio via `host.docker.internal`.

- [ ] **Step 1: Failing tests** (parsed YAML, not substrings): CI has the eval and gate steps in order after pytest and every `uses:` is SHA-pinned; compose has `api`, and `ollama` only under the `ollama` profile; Dockerfile has a `USER` instruction that is not root.
- [ ] **Step 2: Run** `python -m pytest tests/acceptance/test_ci_and_docker.py -v`. Expected: FAIL.
- [ ] **Step 3: Write** the CI additions and Docker files (deployer role).
- [ ] **Step 4: Run** the acceptance tests, then `docker build -t eval-first-rag .` and `docker compose config`. Expected: PASS and a successful build.
- [ ] **Step 5: Commit** (tester tests first, deployer files second).

### Task 14: README, decision records, published results

**Files:**
- Create/Modify: `README.md`, `docs/adr/0002-hybrid-retrieval.md`, `docs/adr/0003-no-rag-framework.md`, `docs/adr/0004-recorded-responses-in-ci.md`
- Test: `tests/acceptance/test_readme.py`

**Interfaces:**
- Produces: README with problem statement, architecture diagram (Mermaid), one-command quick start, the results table (model, hardware, date, every deterministic metric, the judged metrics labeled noisy), known limitations (small-model quality, recorded-response caveat), and how to refresh recordings; three decision records stating what was chosen and what was rejected.

- [ ] **Step 1: Failing tests:** README contains the headings `Results`, `Known limitations`, `Quick start`; the results table names a model, hardware, and a date; every metric name from `EvalResult.metrics` appears in the README or the linked report; no occurrence of the employer name; the three ADR files exist and each contains `Rejected`.
- [ ] **Step 2: Run** `python -m pytest tests/acceptance/test_readme.py -v`. Expected: FAIL.
- [ ] **Step 3: Write** the docs from the committed report; numbers must be copied from `evals/reports/`, never typed from memory.
- [ ] **Step 4: Model gate (optional, only with a yes).** If Niraj approves the roughly 5 GB 7-8B model download, run the eval with it, save the report as `evals/reports/local-7b.md`, and add a second row to the results table. Otherwise the README states that only the small model was measured.
- [ ] **Step 5: Run** `python -m pytest -q`, `python -m ruff check .`, `python -m tools.hygiene`, `python -m tools.role_paths --base <first-commit> --head HEAD`. Expected: all clean.
- [ ] **Step 6: Commit** (tester test first, developer docs second).
- [ ] **Step 7: Approval gate, do not skip.** Ask Niraj before adding a GitHub remote, pushing, or making the repo public.

---

## Self-Review

- **Spec coverage:** hybrid retrieval with fusion and optional reranker (Tasks 4-6); cited answers and refusal (Task 8); harness with the deterministic metrics plus noisy judged ones (Tasks 9-10); regression gate and baseline (Tasks 10, 12, 13); recorded responses so CI needs no model (Tasks 5, 7, 12, 13); published results naming model, hardware, date (Tasks 12, 14); CLI, API, compose with optional Ollama profile (Tasks 11, 13); ADRs and README (Task 14); corpus and golden-set review gates (Tasks 3, 12); repo and workforce conventions (Task 1).
- **Type consistency:** `Hit`, `Chunk`, `Completion`, `SutResult` and `EvalResult.metrics` names match across Tasks 2-12; `ReplayMiss` is defined once (Task 5) and reused by Task 7; metric names in Task 9 match the baseline keys in Tasks 10 and 12.
- **Known assumptions to confirm during build:** Python 3.12 docs text archive layout (Task 3 script may need adjusting); LM Studio's `/v1/embeddings` accepts nomic input without a task prefix (the builder may add the model's recommended prefix and must record it in an ADR); FTS5 availability in the Python build used (verify in Task 4).
