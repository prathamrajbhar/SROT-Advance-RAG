# Checklist — Phase-wise Implementation & Manual QA Gates

A phase is **done** only when every checkbox is ticked AND the manual frontend test (bold, marked 🖐️) passes. Do not start the next phase until done.

**Legend:** [code] = implementation task | 🖐️ = manual frontend verification

**Stack constraints (locked):** AWS S3 only for object storage (LocalStack emulation in dev — never MinIO). Multi-provider model architecture configured purely via `.env` (Anthropic Claude, Google Gemini, OpenAI, Groq, Ollama, vLLM, local embeddings/rerankers). Monorepo orchestration managed via `npm run setup` and `npm run dev`.

---

## Phase 0 — Foundational Setup & Monorepo DX (Days 1–2)

- [code] Monorepo scaffolded: `apps/web`, `apps/api`, `infra`, `docs`, `scripts`
- [code] Root `package.json` with scripts: `npm run setup`, `npm run dev`, `npm run test`, `npm run migrate`
- [code] Automated setup script (`scripts/setup.sh`): verifies `.env`, creates Python venv & installs API dependencies, installs Web npm packages, boots Docker infrastructure (`docker compose up -d`), waits for container health, executes Alembic migrations, and pulls models if local provider selected
- [code] Dev runner: `npm run dev` uses `concurrently` to stream both FastAPI (`:8000`) and Next.js (`:3000`) logs in parallel
- [code] `docker-compose.yml`: postgres, qdrant, redis, **localstack (S3 emulation)**, langfuse, **bge embedder**, **bge reranker**, **whisper**, api, worker, web (and optional ollama profile)
- [code] Pluggable model client architecture initialized with adapter support for Anthropic, Gemini, OpenAI, Groq, Ollama, and vLLM
- [code] Backend boots with `pydantic-settings` validation; missing env (incl. S3 creds, LLM_PROVIDER, respective provider API key or base URL) → crash with clear error
- [code] Boot-time health check verifies: configured LLM provider reachable/valid, embedder + reranker models load, S3 bucket exists/accessible, whisper container healthy
- [code] Alembic initialized; migrations from schema.md applied
- [code] Health endpoints: `/health` (liveness), `/ready` (checks pg / redis / qdrant / s3 / llm_provider / embedder / reranker / whisper individually)
- [code] Structured JSON logging with request-ID middleware
- [code] Frontend: Next.js app with Tailwind, base light theme, no auth yet
- 🖐️ **Manual test:** Run `npm run setup` → finishes with all dependencies and docker containers green → Run `npm run dev` → http://localhost:3000 dashboard shell loads and http://localhost:8000/docs is live → POST /auth/register via Swagger works → `/ready` returns 200 with **pg, redis, qdrant, s3, llm_provider, embedder, reranker, whisper all green** → temporarily corrupt API key or stop local model container → `/ready` shows llm_provider:red and app displays a clean dependency error state (no crash, no fake answer).

---

## Phase 1 — Auth + Projects Shell (Days 3–4)

- [code] User register/login/refresh/logout with refresh-token rotation + reuse detection
- [code] Frontend login/register pages with form validation and error states
- [code] Project CRUD APIs + membership (owner auto-added) per api.md
- [code] Project switcher sidebar; dashboard shows name/description/document count ("0 documents" empty state)
- [code] Route guards: unauthenticated → /login; cross-project access → 404-style "not found in your scope"
- [code] UI states: loading skeletons, empty states with a clear next action, error toasts with `X-Trace-Id`
- 🖐️ **Manual test:** Create account → create 2 projects → rename one → delete one (confirm dialog) → refresh persists state → second user cannot see first user's project.

---

## Phase 2 — Multimodal Ingestion (Days 5–10)

- [code] Upload API accepting multi-file multipart with size/MIME validation per security.md §6
- [code] Content-hash dedupe; idempotent re-uploads create new document version
- [code] Raw files land in S3 under `projects/{pid}/docs/{sha256}/v{n}`; viewer streams via presigned URLs
- [code] Celery worker pipeline: parse → chunk → embed → index
- [code] Parsers: PDF/DOCX (unstructured OSS), MD/TXT (native), XLSX/CSV (row serialization), MP3/MP4 (ffmpeg + faster-whisper large-v3 with timestamps)
- [code] Structure-aware chunker producing parent/child chunks per schema.md
- [code] Embeddings generated via configured embedding provider (local bge-large container or cloud endpoint)
- [code] PII detection step writing `pii_flags`
- [code] Document status endpoint + SSE/polling on frontend with real-time stage + per-file progress
- [code] Frontend upload UI: drag-drop multi-format, per-file progress bar, failure with reason + Retry button, final "Indexed" badge
- [code] PII warning banner on documents that trip the detector
- 🖐️ **Manual test:** Upload one PDF (headings + tables), one DOCX, one MD, one XLSX with a date column, one short MP3, one short MP4 → all reach "Indexed" with live stage transitions. Verify the raw file exists in the S3 bucket (`aws --endpoint-url=$S3_ENDPOINT_URL s3 ls` in dev). Corrupt a PDF manually → status `failed` with human-readable reason; Retry works and re-indexes.

---

## Phase 3 — Hybrid Retrieval + Chat with Citations (Days 11–16)

- [code] `retrieval/hybrid.py`: Postgres FTS BM25 + Qdrant dense; RRF fuse (k=60); unit-test fixture asserting ranking behavior
- [code] Cross-encoder reranker service; reranked top-k contract in API (debug mode returns IDs + scores per api.md §7)
- [code] Conversation memory: follow-up query rewrite via configured LLM provider; last 6 turns in Redis
- [code] Chat endpoint streaming SSE: token → citation → status → final events per api.md §7
- [code] LLM answers in strict JSON mode; server validates every citation ID exists; one repair retry
- [code] Chat UI: message list, real streaming effect, citation chips inline [1], viewer opens on citation click to PDF page / media timestamp / Excel row range
- [code] Empty-project chat returns friendly "Upload documents first" state
- 🖐️ **Manual test:** In the project with the 6 files, ask 3 questions: one factual from the PDF (answer + citation opens exact page), one keyword query dense search alone would miss (exact spreadsheet ID/date), one follow-up ("what about the second one?") verifying context memory. Citation click on MP3 answer seeks to the correct timestamp. Verify switching `.env` between providers (e.g. Gemini, Anthropic, Groq, Ollama) works seamlessly.

---

## Phase 4 — Trust Layer: Confidence + Insufficiency Gate (Days 17–19)

- [code] `confidence/service.py` implementing PRD §8 composite formula with env-configurable weights
- [code] Faithfulness judge call (configured LLM provider, deterministic judge prompt) per answer, inside stream lifecycle ("verifying…" status event)
- [code] `RERANK_MIN_SCORE` env-based insufficiency gate; distinct UI state + searched-doc list
- [code] Answer card: confidence dial (green ≥0.75 / amber 0.50–0.74 / red <0.50), verdict pill (Answered / Insufficient evidence / Unverified), sources-used count, provider badge
- [code] Per-turn scores persisted in `assistant_turns` (audit + feedback loop)
- 🖐️ **Manual test:** Ask a question clearly answerable from docs → green confidence ≥ 0.75. Ask something NOT in the docs → verdict "Insufficient evidence" + searched-docs list, NO invented answer. Temporarily raise `RERANK_MIN_SCORE` via env → same good question flips to insufficient; revert env → returns to answered.

---

## Phase 5 — Evaluation & Observability (Days 20–23)

- [code] Langfuse (self-hosted) wired: every trace has retrieval/rerank/llm spans with provider name, model name, tokens, latency, cost calculation
- [code] Golden Q&A set per project: `docs/eval/<project_slug>.yaml` with ≥ 10 Q&A entries
- [code] Eval worker + API: POST /projects/{id}/eval/run → RAGAS report into `eval_runs` (judge = configured LLM provider)
- [code] CI job runs golden-set eval; fails if faithfulness < 0.90 or context precision < 0.80
- [code] Metrics dashboard per project: faithfulness trend, p95 latency, real-time cost breakdown, ingest failures by error code
- 🖐️ **Manual test:** Trigger eval from UI on one project → run completes with metrics visible. Open Langfuse → click a chat trace → retrieval/rerank/llm spans with model names, exact token counts + latencies. Deliberately bad prompt change on a branch → CI eval fails.

---

## Phase 6 — Security, Rate Limits, Hardening & Prod (Days 24–28)

- [code] ClamAV sidecar; reject/quarantine flow; UI shows "rejected by scan" (`422 SCAN_REJECTED`)
- [code] Rate limits per security.md §9; UI handles 429 with retry-after banner
- [code] Audit emission: uploads, deletes, role changes, logins, 403s, scan rejections, eval triggers
- [code] Invite flow: owner invites email → recipient sees "Join project" → role enforcement verified
- [code] Project deletion cascade verified end-to-end (S3 prefix deleted, Qdrant collection dropped, docs list empty)
- [code] Security headers + CORS env allow-list + HTTPS behind Caddy
- [code] Real S3 buckets replacing LocalStack; swap verified by env change only — no code diff
- [code] S3 versioning + lifecycle rules + bucket-level public-block on prod buckets; scoped IAM principals
- [code] Load test: 50 concurrent chat sessions across 2 projects; p95 first-token < 2.5s on target provider/hardware
- [code] Backup/restore rehearsal (Postgres dump + Qdrant snapshot + S3 versioning) performed once
- 🖐️ **Manual test:** As owner, invite an editor → editor uploads but cannot manage members. Exceed chat rate limit → banner with countdown. Upload the EICAR test file → quarantined visibly. Delete a project in the prod-like environment → objects, vectors, and chats are gone everywhere.

---

## Go/No-Go for Launch

- [ ] All phase 🖐️ checks green, recorded here with date + tester name
- [ ] Single-command developer bootstrap (`npm run setup` and `npm run dev`) verified on fresh environment
- [ ] Golden-set faithfulness ≥ 0.90 on every seed project
- [ ] Zero `unverified` verdict answers in the demo dataset
- [ ] Restore-from-backup tested within the last week
- [ ] CI secret scanner confirms zero plaintext API keys committed in codebase
- [ ] Deploy runbook written; rollback path known
