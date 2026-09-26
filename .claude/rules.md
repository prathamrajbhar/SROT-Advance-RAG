# Rules — Build Contract for SROT (vibe-coding guardrails)

These rules apply to every prompt, every generated file, and every review. If a rule conflicts with a shortcut, the rule wins. If a rule is violated, stop and fix before proceeding.

## 0. Locked Stack Constraints

- **Object storage: AWS S3 only.** LocalStack may emulate S3 in dev (same API, zero code change). MinIO and any other object store are out of scope; no alternative path exists in code or config.
- **Provider-Agnostic Model Architecture:** All model capabilities (LLM generation, evaluation judge, embeddings, reranking, transcription) are cleanly abstracted behind provider adapters and configured purely via environment variables (`.env`). Supports leading cloud providers (Anthropic, Gemini, OpenAI, Groq) and self-hosted engines (Ollama, vLLM, local BAAI models).
- **Monorepo DX Contract:** Developer onboarding and orchestration MUST function with root commands `npm run setup` and `npm run dev`.

## 1. Absolute Prohibitions (Zero-Tolerance)

1. **No fallback logic that masks absence.**
   - Never return model-knowledge answers when evidence is insufficient.
   - When a dependency or model fails, do NOT silently switch to another backend. Surface the dependency/provider name + retry path.
   - If retrieval is weak → verdict `insufficient_evidence`. If a model service is down/rate-limited → clear error card with `Retry-After` if available. "Fallback" is a product verdict, not a silent code path.
2. **No hardcoded secrets or API keys.** All keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, etc.), URLs, model names, thresholds, timeouts, chunk sizes, and prompt text come strictly from env/config/versioned prompt files. Plaintext secrets in codebase are forbidden and blocked by CI.
3. **No dummy or placeholder data.**
   - No `Lorem ipsum`; no fake citation counts; no "TODO: fill in later" UI content; no hardcoded rows that pretend to be analytics.
   - Example content only lives in clearly-marked fixtures under `tests/` or `docs/eval/`.
4. **No silent catches.** Every error path logs with context (trace_id, user_id, project_id), re-raises or maps to a typed HTTP error, and is visible. `except: pass` is banned.
5. **No magic numbers.** Every literal in logic is a named constant with a comment, or loaded from config.

## 2. Code Quality Bar

- **Types everywhere:** no `any` / `# type: ignore` without a justification comment. Backend: Pydantic + typed returns. Frontend: strict TypeScript.
- **One source of truth per concern:** config schema lives in `apps/api/core/config.py`; prompts in `core/prompts/` versioned files; retrieval constants in `modules/retrieval/constants.py`.
- **Small files:** if a Python/TS file exceeds ~300 lines, split it into modular subcomponents.
- **Module boundary:** routers call services; services call repositories/clients. No DB or HTTP logic in router files.
- **Pure-named functions:** verb-led (`embed_chunk`, `rerank_candidates`, `compute_confidence`), not `do_stuff`, `handle_it`.
- **No dead code:** unused imports, commented blocks, stale TODOs are removed before commit.
- **Idempotency:** every write endpoint is safe to retry (content hashes, UUIDs, upserts, dedupes).
- **Determinism in tests:** seed all randomness; live model tests are marked `smoke` and skipped by default in unit suites.

## 3. Model & Provider Rules

- All model calls go through `core/models/` unified clients (`BaseLLMClient`, `BaseEmbedder`, `BaseReranker`, `BaseWhisper`). No module imports vendor SDKs directly.
- Every model call carries: explicit timeout budget, max-retries=2 with exponential backoff, and full telemetry tracing to Langfuse.
- Model answers are never rendered directly to UI without going through the SSE/citation validation layer.
- Judge prompts (faithfulness) are versioned files; a changed prompt without a passing golden-eval run does not merge.
- Model names and provider targets are configured via `.env` (`LLM_PROVIDER`, `LLM_MODEL`, `EMBEDDING_PROVIDER`, etc.).
- Active provider health is surfaced on `/ready`.

## 4. UI Contract (Clean, Light, Enterprise)

- Light theme only. No dark-mode toggle in scope.
- No glassmorphism, decorative gradients, neon colors, particle effects, or heavy shadows.
- Typography: Inter (or system fallback) at 400/500/600 weights only.
- Colors: one primary action color, one danger color, semantic grays; status tokens only: green (ok), amber (warning), red (error), neutral gray-500.
- Layouts: 3-pane app (sidebar → main → right rail); max content width 1440px; generous whitespace; real labels ("Upload documents", "Confidence"); no emoji in UI.
- States: every interactive element has hover/focus/disabled/loading states; every list has an empty state with a clear next action; every error surfaces `X-Trace-Id`.
- Streaming answers render progressively with inline citation chips; never fake-typewriter without real stream data.
- Numbers are real: citation counts, token counts, latencies, confidence values, cost estimates come from API payloads — or are not shown.

## 5. API & Data Contracts

- Errors follow RFC 7807: `{ type, title, status, detail, trace_id }` for all 4xx/5xx.
- Paginated lists (`page`, `page_size`, `total`); no unbounded queries.
- All datetimes ISO-8601 UTC; cost fields = accurate token or compute pricing in USD (`cost_usd`); UI formats locale-aware.
- OpenAPI auto-generated; SDK client generated from schema — API contracts live in api.md, not in frontend files.
- Every mutation writes an `audit_events` row.

## 6. Testing & Eval Discipline

- Happy-path tests are necessary, not sufficient: retrieval and citation logic also need failure cases (empty corpus, below-threshold scores, malformed LLM JSON output).
- Golden eval set per project exists before Phase 5 completion.
- CI gates: type check, lint, unit tests, golden RAGAS thresholds per checklist.md.
- No test asserts a magic number it computed itself; fixtures encode intent.
- API-contract tests validate shapes from api.md; a doc-code drift is a failing test, not a guess.

## 7. Vibe-Coding Workflow Rules

When prompting an AI code assistant (or self):

1. **One phase at a time.** State the current phase; don't ask for Phase 5 work while Phase 2 is untested.
2. **Show schema first.** Before an endpoint, agree on the Pydantic schema + DB row shape (from schema.md).
3. **Demand contracts.** Request/response shapes before bodies; function signatures before bodies; SQL before ORM if ambiguous.
4. **Verify per phase.** Use checklist.md 🖐️ items as acceptance criteria; describe real failures (screenshots, SSE transcripts, `/ready` output) back into the prompt — never just "it doesn't work."
5. **No unexplained output.** Non-trivial design choices (why RRF k=60, why these chunk sizes) must be explained or linked to architecture.md.
6. **Migration discipline.** Every schema change = Alembic migration; never edit the DB manually.
7. **Prompt versioning.** LLM/judge prompt changes are commits under `core/prompts/v{n}/` with a CHANGELOG entry; CI regression (Phase 5 gates) must pass before merge.
8. **Git hygiene.** One logical change per commit; conventional commits (`feat:`, `fix:`, `chore:`); no `print()`/`console.log` leftovers.

## 8. Performance & Cost Guardrails

- Total per-chat timeout budget is explicit, enforced, and distributed across stages (retrieval/rerank/generation/verification) — never a single unbounded await.
- Every response returns token counts and `cost_usd`; daily aggregate visible on the admin dashboard.
- Retrieval caps: hybrid top-K=40, rerank top-K=8, parents ≤ 8, final context ≤ configured token budget.
- No unbounded loops over pages/files/chunks without streaming or pagination.

## 9. Docs-First Discipline

- Every feature references: PRD requirement ID + architecture section + schema table it touches.
- Before a phase is marked done, `checklist.md` items are ticked and cross-docs updated if design/schema/security surface changed.
- `docs/CHANGELOG.md` updated at each phase completion.

## 10. When in Doubt

Ask one of these deciding questions:
- Can I observe and measure this behavior? If not, add tracing/metrics first.
- Would an on-call engineer reading this at 2am know what it does? If not, tighten names/logs/docs.
- Could I demo this exact screen to a paying customer without embarrassment? If not, fix empty/loading/error states before adding features.
