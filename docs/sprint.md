# Agile Sprint Plan & Milestone Execution Guide

## Project: SROT (Advanced Multimodal Enterprise RAG)
**Document Version:** 1.1.0  
**Status:** Approved for Agile Execution  
**Methodology:** Agile Scrum (Sprint-by-Sprint Incremental Delivery)  
**Quality Bar:** Production-Grade (Zero "Vibe Coding", Full TDD, Enterprise Light Theme)  

---

## 1. Definition of Done (DoD) for Every Sprint

Every task and sprint in SROT must satisfy these strict quality gates before being marked complete:
1. **Zero TypeScript Errors:** `npm run typecheck` passes with zero errors (`noImplicitAny`, strict mode).
2. **Zero Failing Unit/Integration Tests:** `pytest apps/api/tests/` passes 100%.
3. **No File Over 200 Lines:** Every file adheres to single responsibility; components and routers split logically.
4. **Strict Enterprise Light Design:** All UI components implement Default, Hover, Focus-Visible, Active, Disabled, Loading (skeleton shimmer), and Empty states using the slate/zinc monochromatic palette.
5. **No Undocumented Dependencies:** Every npm or pip package must be explicitly listed with its exact version in `requirements.txt` or `package.json`.
6. **No Console Logs or Plaintext Secrets:** Zero `console.log` statements in frontend; zero unmasked secrets in API responses.

---

## 2. Sprint Roadmap Overview

```
[Sprint 0: Tooling & Vault] ──> [Sprint 1: Onboarding & BYOK] ──> [Sprint 2: Direct S3 & Celery]
              │
              ▼
[Sprint 3: Docs & Qdrant]   ──> [Sprint 4: Tabular & DuckDB]  ──> [Sprint 5: Audio & Video]
              │
              ▼
[Sprint 6: Retrieval & UI]  ──> [Sprint 7: Ragas & Hardening] ──> [v1.0 Production Launch]
```

---

## 3. Detailed Sprint Breakdown

### Sprint 0: Infrastructure, Database & Cryptographic Vault
- **Goal:** Establish multi-tenant database models, Qdrant & Redis containers, AWS S3 connectivity, and the AES-256-GCM secret vault.
- **User Stories & Tasks:**
  - `S0-1`: Update `infra/docker-compose.yml` to include `qdrant/qdrant:v1.19.1` and `redis:7.4-alpine`.
  - `S0-2`: Implement `apps/api/core/crypto.py` with AES-256-GCM envelope encryption, nonce generation, and secret masking.
  - `S0-3`: Implement SQLAlchemy 2.0 Async models (`Tenant`, `Workspace`, `User`, `ProviderSetting`, `Document`, `DocumentChunk`, `ProcessingJob`, `QuerySession`).
  - `S0-4`: Configure Alembic migration scripts and run initial baseline migration against PostgreSQL 16.
  - `S0-5`: Write unit tests for AES-256 vault (`test_crypto.py`) validating encryption, decryption, and tampering detection.
- **Verification Criteria:**
  - Docker services spin up cleanly (`qdrant`, `redis`, `postgres`).
  - `pytest apps/api/tests/test_crypto.py` passes with 100% coverage.

---

### Sprint 1: Multi-Tenant Onboarding, BYOK Vault & Sample Dataset Seeder
- **Goal:** Deliver the 5-step SaaS onboarding wizard, provider adapters (Cloud APIs + Local Ollama/vLLM) with real-time health checks, and the one-click sample data seeder.
- **User Stories & Tasks:**
  - `S1-1`: Implement dynamic Provider Adapters (`modules/providers/`) for OpenAI, Gemini, Anthropic, Groq, and Ollama/vLLM.
  - `S1-2`: Implement `POST /api/v1/onboarding/test-provider` endpoint executing live model pings with latency measurement.
  - `S1-3`: Implement `POST /api/v1/onboarding/provider-settings` storing AES-256 encrypted credentials in PostgreSQL.
  - `S1-4`: Build the 5-step Next.js 15 Onboarding Wizard in `apps/web/src/components/onboarding/` adhering to the Enterprise Light Design System.
  - `S1-5`: Integrate interactive "Test Connection" button with real-time status pills (Testing / Healthy / Error).
  - `S1-6 (NEW - Item 7)`: Implement `POST /api/v1/onboarding/seed-sample-data` and frontend **"Load Enterprise Sample Dataset"** button on Step 5 of the wizard, preloading verified multi-modal test files (Excel, PDF, MP4, MP3) for instant exploration.
- **Verification Criteria:**
  - Entering a test API key or local Ollama URL verifies successfully and displays green diagnostic latency.
  - Clicking "Load Enterprise Sample Dataset" seeds test files to tenant S3 prefix and enqueues indexing.

---

### Sprint 2: Direct-to-S3 Multipart Ingestion & Real-Time Redis SSE Stream
- **Goal:** Enable multi-gigabyte client-side parallel chunk uploads to AWS S3, set up background Celery workers, and stream live progress via Server-Sent Events (SSE).
- **User Stories & Tasks:**
  - `S2-1 (NEW - Item 2)`: Implement S3 Multipart Presigned engine in `apps/api/core/s3.py` supporting `InitiateMultipartUpload`, `PresignPartUpload` (10MB chunks), and `CompleteMultipartUpload`.
  - `S2-2`: Implement Celery worker configuration (`core/celery_app.py`) with Redis broker and queue segregation (`celery-media`, `celery-docs`, `celery-default`).
  - `S2-3`: Implement `POST /api/v1/documents/multipart/initiate`, `POST /api/v1/documents/multipart/presign-parts`, and `POST /api/v1/documents/multipart/complete`.
  - `S2-4 (NEW - Item 2)`: Build Next.js 15 S3 Multipart Dropzone with parallel part chunking, pause/resume, and retry capability.
  - `S2-5`: Build Document Catalog table (`/workspace/[id]/documents`).
  - `S2-6 (NEW - Item 6)`: Implement Redis Pub/Sub progress broadcaster and FastAPI SSE endpoint `GET /api/v1/documents/:id/progress-stream`; integrate `useEventSource` in Next.js to stream progress without database polling.
- **Verification Criteria:**
  - A 200MB video uploads cleanly in parallel 10MB chunks directly to AWS S3.
  - Ingestion progress bar updates continuously in real-time via SSE without polling PostgreSQL.

---

### Sprint 3: Document Extractors, Visual Bounding Boxes & Qdrant Hybrid Indexing
- **Goal:** Implement layout-aware PDF and DOCX extraction with normalized bounding box coordinates, parent-child chunking, and initialize Qdrant with on-disk HNSW and scalar quantization.
- **User Stories & Tasks:**
  - `S3-1 (NEW - Item 3)`: Implement `modules/ingestion/extractors/pdf_extractor.py` using `docling` (v2.123.1) and `pymupdf` (v1.28.2) extracting layout order, table structures, and normalized page bounding box coordinates `[ymin, xmin, ymax, xmax]`.
  - `S3-2`: Implement `modules/ingestion/extractors/docx_extractor.py` for Word documents.
  - `S3-3 (NEW - Item 3)`: Implement Hierarchical Parent-Child Chunker (`modules/ingestion/chunker.py`) generating child chunks with bounding box metadata linked to parent sections.
  - `S3-4`: Initialize Qdrant collection `srot_enterprise_rag` with dense + sparse BM25 vectors, on-disk HNSW, and scalar quantization (`int8`).
  - `S3-5`: Implement Celery task `process_document_task` indexing chunks into Qdrant with tenant payload tags.
- **Verification Criteria:**
  - PDF tables are extracted into structured Markdown; bounding boxes are stored in Qdrant payloads and DB records.

---

### Sprint 4: Tabular Engine (Deterministic DuckDB Text-to-SQL)
- **Goal:** Eliminate mathematical hallucinations on spreadsheets by indexing schemas into Qdrant and executing analytical queries in DuckDB.
- **User Stories & Tasks:**
  - `S4-1`: Implement `modules/ingestion/extractors/excel_extractor.py` with `openpyxl` and `duckdb`, converting sheets into Parquet stored in S3.
  - `S4-2`: Extract table schema, column summaries, and sample rows; index semantic table definitions in Qdrant.
  - `S4-3`: Implement `modules/agents/sql_agent.py` generating read-only DuckDB SQL with strict AST keyword whitelisting.
  - `S4-4`: Build UI Tabular Data Grid previewer in Next.js 15 displaying executed SQL, row counts, and interactive column sorting.
- **Verification Criteria:**
  - Asking *"What was the total Q3 profit?"* triggers the SQL agent, executes DuckDB SQL, and returns 100% exact mathematical figures.

---

### Sprint 5: Audio & Video Multimodal Pipeline
- **Goal:** Ingest video and audio files, extract timestamped transcripts and visual keyframes, and provide interactive seekable playback in the UI.
- **User Stories & Tasks:**
  - `S5-1`: Implement `modules/ingestion/extractors/audio_extractor.py` using `faster-whisper` (v1.2.1) with word-level timestamps.
  - `S5-2`: Implement `modules/ingestion/extractors/video_extractor.py` using `ffmpeg` + `scenedetect` (v0.7.1) for scene cuts and keyframe extraction to S3.
  - `S5-3`: Implement temporal multimodal fusion aligning visual descriptions with speech transcript windows `[start_t, end_t]`.
  - `S5-4`: Build HTML5 Video Player and Audio Waveform Player components with programmatic timestamp seek.
- **Verification Criteria:**
  - An MP4 video is transcribed and segmented; clicking a timestamp badge `[VID: 04:12]` in the UI navigates video player to that exact second.

---

### Sprint 6: Advanced Retrieval, FlashRank Reranker & Split-View UI (Bounding Box Overlays)
- **Goal:** Build the two-stage hybrid retrieval pipeline, FlashRank cross-encoder reranker, grounded synthesizer, and the split-view analytical chat UI with visual bounding box highlights.
- **User Stories & Tasks:**
  - `S6-1`: Implement Agentic Query Router classifying queries (Semantic vs. Analytical Tabular vs. Temporal Media).
  - `S6-2`: Implement Qdrant Hybrid Search (Dense + Sparse BM25) with tenant payload filters.
  - `S6-3`: Integrate `flashrank` (v0.2.10) cross-encoder reranking, filtering low-scoring candidate chunks.
  - `S6-4`: Implement Grounded Synthesizer with parent-child context expansion and anti-hallucination citation tags.
  - `S6-5 (NEW - Item 3)`: Build Next.js 15 Enterprise Light Chat view (`/workspace/[id]/chat`) with streaming response, slide-over Split-Pane Drawer, and dynamic translucent canvas bounding box highlight overlays on the PDF Viewer tab.
- **Verification Criteria:**
  - End-to-end question answering yields sub-350ms retrieval latency; clicking a PDF citation displays the page with the translucent bounding box highlight.

---

### Sprint 7: Observability, Ragas Benchmark & Production Hardening
- **Goal:** Validate retrieval quality using automated Ragas metrics, enforce rate-limiting, audit logging, and perform end-to-end security audits.
- **User Stories & Tasks:**
  - `S7-1`: Implement automated RAG evaluation harness using `ragas` (v0.4.3) measuring Faithfulness, Answer Relevance, and Context Precision.
  - `S7-2`: Build Analytics Dashboard (`/workspace/[id]/analytics`) displaying real-time retrieval benchmarks and latency metrics.
  - `S7-3`: Perform OWASP security audit: verify AES-256 vault, SQL AST sanitization, and S3 multipart presigned URL expiration.
  - `S7-4`: Run end-to-end test suite (`npm run typecheck`, `npm run build`, `pytest`).
- **Verification Criteria:**
  - Ragas benchmark achieves $\ge 95\%$ Faithfulness and $\ge 90\%$ Context Precision.
  - Production build succeeds cleanly with 0 linter warnings or TypeScript errors.
