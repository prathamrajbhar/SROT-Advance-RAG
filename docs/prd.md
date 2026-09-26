# PRD — Enterprise Multi-Project Multimodal RAG Platform

**Product name:** SROT
**Version:** 2.0 | **Date:** Sep 2026 | **Status:** Approved for build

**Hard stack constraints (locked):** AWS S3 only for object storage (LocalStack emulation in dev — never MinIO). Provider-agnostic AI model architecture configured entirely via environment variables (`.env`) — supports both enterprise cloud providers (Anthropic Claude, Google Gemini, OpenAI, Groq, Mistral) and self-hosted inference (Ollama, vLLM, local embeddings/rerankers). Monorepo orchestration managed via root npm scripts (`npm run setup`, `npm run dev`).

---

## 1. Problem Statement

Teams store critical knowledge in scattered formats — PDFs, Word docs, Markdown, Excel sheets, recorded meetings (MP4), and audio notes (MP3). Basic RAG demos can answer questions from a single PDF, but they break down in real organizations:

- No multi-project isolation or permissions
- Only text formats supported (no audio/video/spreadsheets)
- Naive chunking destroys document structure
- Vector-only retrieval misses keyword-heavy queries
- No citations, no confidence signals — users can't trust answers
- Hardcoded or vendor-locked LLM integrations that cannot easily switch between cost-effective local models and high-intelligence cloud APIs
- Fragmented developer experience across backend, frontend, models, and docker infra
- No evaluation pipeline, so quality silently degrades

## 2. Product Vision

A multi-tenant platform where users create **projects** (isolated knowledge bases), upload files of any supported format, and chat with grounded, cited, confidence-scored answers. Every layer — ingestion, retrieval, generation, evaluation — is built to production standards, fully measurable, and observably working. 

SROT decouples business logic from specific AI providers: teams can switch between local inference (Ollama / vLLM) for zero-data-egress compliance, or top-tier cloud models (Anthropic Claude, Google Gemini, OpenAI, Groq) for maximum reasoning accuracy, all simply by adjusting environment variables.

Furthermore, SROT delivers a zero-friction developer workflow in a unified monorepo: running `npm run setup` automatically bootstraps all Python/Node dependencies, checks/pulls required Docker services and models, and runs DB migrations. Running `npm run dev` concurrently boots the entire platform (FastAPI backend + Next.js frontend + background workers).

## 3. Goals & Non-Goals

### Goals
- Multi-project workspace with per-project knowledge isolation
- Multimodal ingestion: PDF, DOCX, MD, TXT, XLSX/CSV, MP3, MP4
- Hybrid retrieval (dense + sparse BM25) with cross-encoder reranking
- Streaming answers with **evidence-backed citations** (file name + page/timestamp/row range)
- **Confidence score** per answer + explicit "insufficient evidence" verdict — never hallucinated fallback
- **Provider-agnostic LLM & AI architecture**: Swappable generation, query-rewriting, and evaluation judge via standard `.env` configuration (Anthropic, Gemini, OpenAI, Groq, Ollama, vLLM)
- **Seamless Monorepo Developer Experience**: Single-command setup (`npm run setup`) for all packages/models/containers and single-command local orchestration (`npm run dev`)
- RAGAS-based evaluation with regression testing in CI
- Full observability (tracing, latency, exact token/compute-cost) via self-hosted Langfuse
- Ingestion pipeline with structure-aware chunking, dense vector embeddings, and audio transcription (faster-whisper)

### Non-Goals (v1)
- Real-time collaborative editing of documents
- Auto-generated document authoring
- On-device / offline mobile inference
- Public/anonymous project sharing (v2)

## 4. Personas

| Persona | Need |
|---|---|
| Knowledge Worker | Ask questions across client docs, get answers with sources they can verify |
| Project Lead | Isolate client/legal docs per project, control who accesses them |
| Solo Builder / Consultant | Keep multiple projects (clients) separated in one account, switch LLM backend to balance speed/cost |
| Platform Admin | Monitor quality metrics, compute/API cost, model latency, and ingestion health |

## 5. Core User Flows

1. **Setup & Boot** → `npm run setup` → `npm run dev` → fully operational local app
2. **Create Project** → name, description → empty workspace
3. **Upload Files** → drag & drop multiple formats → live ingestion status (queued → parsing → chunking → embedding → indexed / failed with reason)
4. **Chat** → select project → ask question → streaming answer with inline citations + confidence dial
5. **Verify** → click citation → viewer opens file at exact page (PDF), timestamp (audio/video), or row range (Excel)
6. **Inspect Quality** → per-answer meta drawer showing faithfulness, retrieval scores, provider & model metadata, and sources used
7. **Manage** → delete file → cascade removes S3 object + vectors; rename project; view eval dashboard

## 6. Functional Requirements (by Phase)

### P0 — Foundation & Monorepo DX
- FR-1: Email/password signup-login, JWT access + refresh token
- FR-2: Project CRUD (create/rename/delete), project switcher
- FR-3: Clean light-themed UI shell: sidebar (projects), main pane, chat pane
- FR-4: Boot-time readiness gate across Postgres, Redis, Qdrant, S3, and configured AI services (LLM, Embedder, Reranker)
- FR-4.1: Unified root `package.json` with scripts: `npm run setup` (installs backend venv/poetry/uv, frontend npm deps, starts docker services, runs DB migrations, checks/pulls model assets) and `npm run dev` (concurrently runs backend FastAPI and frontend Next.js)

### P1 — Ingestion
- FR-5: Multipart upload with per-file progress; raw objects stored in S3 under `projects/{pid}/docs/{sha256}/v{n}`
- FR-6: Format routing: `unstructured` OSS (PDF/DOCX), native (MD/TXT), openpyxl-style row serialization (XLSX/CSV), faster-whisper via ffmpeg audio extraction (MP3/MP4)
- FR-7: Structure-aware chunking: headings, tables, lists preserved; parent–child chunks
- FR-8: Embeddings generated via configured embedding provider/service (defaulting to local `bge-large-en-v1.5` or configured cloud endpoint)
- FR-9: Metadata per chunk: project_id, doc_id, doc_name, page_number OR timestamp range OR row range, chunk index, content hash
- FR-10: Live ingestion status in UI via polling or SSE; failures show exact reason + Retry

### P2 — Retrieval & Chat
- FR-11: Hybrid search: BM25 (Postgres FTS) + dense Qdrant ANN, fused with RRF (k=60)
- FR-12: Cross-encoder reranking on top-40 fused results → top 8 candidates
- FR-13: Conversational memory: follow-up question rewriting via configured LLM provider using last 6 turns
- FR-14: SSE streaming chat with inline numbered citations and real-time token delivery
- FR-15: Citation click → file viewer at exact page/timestamp/row

### P3 — Trust Layer
- FR-16: Confidence score per answer (composite, see §8)
- FR-17: Faithfulness judge per response executed via configured LLM provider with deterministic judge prompt
- FR-18: When top reranker score < env threshold → verdict `insufficient_evidence` + list of searched docs — never hallucinate, never fall back to general model training data

### P4 — Evaluation & Observability
- FR-19: Langfuse (self-hosted) traces for every request recording provider, model, latency, tokens, and accurate cost
- FR-20: Golden Q&A eval set per project; CI job runs RAGAS (faithfulness, context precision/recall, answer relevancy) and fails build below thresholds
- FR-21: Metrics dashboard: avg faithfulness, p95 latency, real API/compute cost breakdown, verdict distribution per project

### P5 — Hardening
- FR-22: Query-time permission filtering at the vector index layer
- FR-23: Per-user rate limits, upload size limits, ClamAV malware + PII scan before indexing
- FR-24: Audit log: uploads, deletes, project access changes, 403s

## 7. Non-Functional Requirements

| Category | Requirement |
|---|---|
| DX / Setup | `npm run setup` initializes all prerequisites and dependencies cleanly; `npm run dev` starts all dev servers concurrently with zero config hassle |
| Latency | First token < 2s (streaming), full answer < 12s p95 (under target provider & network conditions) |
| Ingestion | 100-page PDF indexed in < 90s; 30-min audio transcribed in < 2min |
| Reliability | Ingestion retries 3x with backoff; failed jobs never silently disappear |
| Cost | Accurate real-time cost accounting (`cost_usd`) calculated per model provider token rates or local compute metrics |
| Scalability | Workers scale horizontally; project isolation survives 10k+ docs/project |
| Observability | 100% of model calls traced in Langfuse with model name, tokens, latency, and costs |
| Code quality | Zero hardcoded values, zero dummy data, zero fallback hacks (see rules.md) |

## 8. Confidence Score Specification

```
confidence = 0.45 * faithfulness
           + 0.30 * top_reranker_score (normalized 0–1)
           + 0.15 * retrieval_coverage (% of answered claims with supporting chunk)
           + 0.10 * (1 - latency_penalty)
```

- ≥ 0.75 → green "High confidence"
- 0.50–0.74 → amber "Moderate — verify citations"
- < 0.50 → red "Low — likely insufficient evidence"
- Confidence shown next to every answer; stored on `assistant_turns` for audit.

## 9. Success Metrics

- Single-command dev onboarding (`npm run setup` → `npm run dev` passes out-of-the-box)
- Faithfulness ≥ 0.90 on every project's golden set
- Context precision ≥ 0.80 on golden set
- Citation click-through > 40% (users actually verifying)
- Zero answers served with citations that fail server-side validation
- Transparent cost & latency attribution across all configured LLM providers

## 10. Release Criteria (per phase)
Each phase ships only when **all frontend-manual checkpoints in checklist.md pass**. No phase starts until the previous phase's checkpoints are green.
