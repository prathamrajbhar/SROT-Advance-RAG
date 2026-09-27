# Product Requirements Document (PRD)

## Project Name: SROT (Advanced Multimodal Enterprise RAG)
**Document Version:** 1.1.0  
**Status:** Approved for Agile Execution  
**Target Release:** Enterprise SaaS v1.0  

---

## 1. Executive Summary & Vision

Modern enterprises operate on fragmented, heterogeneous data spanning scanned PDF contracts, financial Excel spreadsheets, technical presentations, training videos, and recorded client calls. Current off-the-shelf RAG solutions fail in three critical areas:
1. **Multimodal Blindspots:** They treat everything as flat text, discarding PDF layouts, audio/video timestamps, visual diagrams, and bounding-box coordinates.
2. **Tabular & Calculation Hallucinations:** Traditional vector similarity search is mathematically incapable of answering analytical spreadsheet questions like *"What is the sum of Q3 revenues across Europe?"*.
3. **Enterprise Privacy & SaaS Flexibility:** Enterprises are hesitant to send sensitive data to one-size-fits-all cloud LLMs without Bring-Your-Own-Key (BYOK) security or local self-hosted (Ollama/vLLM) options.

**SROT** is an enterprise-grade, multi-tenant SaaS Multimodal RAG platform engineered for maximum retrieval accuracy and massive scale. It provides verified, citation-grounded intelligence across PDF, DOCX, Excel/CSV, Images, Audio, and Video with:
- **Pure AWS S3 Storage & S3 Multipart Presigned Uploads** for resilient, chunked upload of 1GB+ files.
- **Visual Bounding Box Grounding** on PDFs with exact normalized coordinates for instant audit verification.
- **Real-Time Server-Sent Events (SSE)** streaming ingestion progress from Redis pub/sub.
- **One-Click Enterprise Sample Dataset** in the onboarding flow for zero-friction testing.
- **Dual-Representation Tabular Engine** using DuckDB Text-to-SQL for 100% deterministic mathematical accuracy.
- **Temporal Video & Audio Fusion** with interactive timestamp deep-linking.
- **AES-256-GCM BYOK Vault** supporting both Cloud APIs (OpenAI, Gemini, Anthropic) and Local/Private engines (Ollama, vLLM).
- **High-Density Enterprise Light Design** that eliminates AI novelty gimmicks in favor of clean, professional analytical tooling.

---

## 2. Target Personas & Use Cases

### 2.1 Personas
1. **Enterprise Financial / Operations Analyst:** Needs to upload 50+ Excel sheets and quarterly PDFs, performing complex aggregations and cross-referencing audit figures with zero math hallucination.
2. **Legal & Compliance Counsel:** Reviews dense PDF contracts, patents, and scanned addendums. Requires exact page citations with bounding-box visual proof highlighted directly on the rendered page.
3. **Technical Lead / Product Architect:** Searches through hours of recorded technical presentations and architecture videos to locate specific technical decisions and diagrams.
4. **Tenant Workspace Administrator:** Responsible for managing team access, setting model provider credentials (BYOK), configuring privacy boundaries, and monitoring RAG retrieval accuracy.

### 2.2 Primary Use Cases
- **Multi-Modal Synthesis:** Ask *"What did the CEO announce in the Q2 video keynote regarding the APAC expansion, and how does it compare to the expenses in the Q2 financial sheet?"* $\rightarrow$ SROT retrieves the video segment at `04:12` and executes a deterministic DuckDB SQL query on `financials.xlsx`, returning a unified synthesized answer with interactive citations.
- **Direct Citation Verification:** Clicking on any citation opens the exact PDF page with a bounding box highlight, seeks the video player to the specific second, or reveals the executed DuckDB SQL trace.

---

## 3. Product Scope & Functional Requirements

### Epic 1: Multi-Tenant SaaS, BYOK & Zero-Friction Onboarding
- **FR-1.1:** Support Organization $\rightarrow$ Workspace $\rightarrow$ User hierarchical multi-tenancy.
- **FR-1.2:** Guided 5-step onboarding wizard for workspace setup.
- **FR-1.3:** BYOK Model Configuration:
  - Cloud Providers: OpenAI, Google Gemini, Anthropic Claude, Groq.
  - Local / Self-Hosted: Ollama, vLLM, custom OpenAI-compatible endpoints.
  - Hybrid Mode: Local embeddings + Cloud synthesis or vice versa.
- **FR-1.4:** Real-time **"Test Connection"** health check before saving credentials.
- **FR-1.5:** AES-256-GCM envelope encryption at rest for all credentials.
- **FR-1.6 (NEW - Item 7):** **"Load Enterprise Sample Dataset"** button on the final onboarding step, bundling a pre-verified test pack (1 financial Excel workbook, 1 multi-column technical PDF with tables, 1 30-second demo MP4 video, and 1 MP3 audio memo) for immediate end-to-end testing within 10 seconds of signup.

### Epic 2: Direct-to-S3 Resilient Ingestion & Real-Time SSE
- **FR-2.1:** Support file formats:
  - Documents: `.pdf`, `.docx`, `.txt`, `.md`
  - Spreadsheets: `.xlsx`, `.xls`, `.csv`
  - Audio: `.mp3`, `.wav`, `.m4a`
  - Video: `.mp4`, `.mkv`, `.mov`, `.webm`
  - Images: `.png`, `.jpg`, `.jpeg`, `.webp`
- **FR-2.2 (NEW - Item 2):** **S3 Multipart Presigned Uploads** for large files ($>50\text{MB}$):
  - API provides endpoints to initiate multipart upload, presign individual 10MB chunk parts, and complete the multipart upload.
  - Frontend uploads chunks in parallel with retry per chunk and pause/resume capability, eliminating VPN upload dropouts for 1GB+ video files.
- **FR-2.3 (NEW - Item 6):** **Server-Sent Events (SSE) Ingestion Progress Stream** (`GET /api/v1/documents/:id/progress-stream`):
  - Ingestion workers publish granular progress events to Redis Pub/Sub (`EXTRACTING: 35%`, `WHISPER_TRANSCRIBING: Segment 4/12`, `KEYFRAMES_CAPTURED: 8`, `QDRANT_INDEXING: 90%`, `READY: 100%`).
  - Eliminates repetitive polling against the PostgreSQL database.

### Epic 3: Specialized Extraction & Visual Grounding
- **FR-3.1 (PDF & Docs):** Layout-aware extraction using Docling and PyMuPDF, preserving table structures, headers, and OCR text from scanned documents.
- **FR-3.2 (NEW - Item 3):** **Visual Bounding Box Grounding**:
  - Every extracted text block, paragraph, and table records normalized page coordinates `[ymin, xmin, ymax, xmax]` in `document_chunks.bounding_box`.
  - Stored in Qdrant and relational chunk records to render visual overlays in the UI.
- **FR-3.3 (Excel & Tabular):** Dual indexing:
  1. Extract table schema, column descriptions, and summary stats into Qdrant for semantic discovery.
  2. Register tables into in-process DuckDB for exact Text-to-SQL mathematical queries.
- **FR-3.4 (Audio):** Transcribe speech using Faster-Whisper with word- and segment-level timestamps.
- **FR-3.5 (Video):** Extract audio track for Whisper transcription + PySceneDetect keyframe extraction + Vision captioning, fusing them into synchronized temporal multimodal chunks.
- **FR-3.6 (Images):** Extract visual captions, OCR text, and diagrams.

### Epic 4: High-Accuracy Hybrid Retrieval & Reranking
- **FR-4.1:** Agentic query intent router: classifies query as semantic, analytical/quantitative, temporal media, or multi-hop.
- **FR-4.2:** Qdrant hybrid retrieval: Dense vector search (semantic similarity) + Sparse lexical search (BM25/SPLADE for exact terms/IDs) filtered strictly by `tenant_id` and `workspace_id`.
- **FR-4.3:** Two-stage Cross-Encoder Reranking using FlashRank (local ONNX) or Cohere Rerank v3, filtering candidates below a strict relevance threshold.
- **FR-4.4:** Hierarchical Parent-Child context expansion to eliminate the "Lost in the Middle" syndrome.

### Epic 5: Enterprise Light UI & Split-View Source Inspector
- **FR-5.1:** Clean, high-density Enterprise Light theme (zinc/slate palette, no AI neon gradients, high legibility).
- **FR-5.2:** Streaming conversational chat with markdown formatting and inline citation badges.
- **FR-5.3:** Interactive Split-Pane / Drawer displaying:
  - **PDF Viewer with Bounding Box Overlay**: Draws a translucent highlight over the exact source passage.
  - **HTML5 Video Player**: Deep-links to exact timestamp seek (`?t=142s`).
  - **Audio Player**: Waveform player with synchronized transcript.
  - **Tabular Data Grid**: Displays DuckDB query results and executed SQL queries.

---

## 4. Non-Functional Requirements (NFRs)

| Category | Requirement | Target Metric |
| :--- | :--- | :--- |
| **Performance** | Hybrid retrieval latency (Qdrant + FlashRank) | P95 < 350ms |
| **Performance** | Time to First Token (TTFT) on Cloud LLMs | P95 < 800ms |
| **Scalability** | Vector database volume capacity | > 10,000,000 vectors with on-disk HNSW & quantization |
| **Scalability** | S3 Multipart Upload resilience | Up to 2GB per video with 0% network timeout failures |
| **Streaming** | Ingestion progress latency (SSE via Redis) | < 100ms update latency to UI |
| **Data Security** | Credential encryption at rest | AES-256-GCM with master key envelope |
| **Data Security** | Multi-tenant isolation | 100% tenant isolation in DB, S3 prefixes, and Qdrant |
| **Accuracy** | Ragas Evaluation Benchmark | Faithfulness $\ge 95\%$, Context Precision $\ge 90\%$ |
| **Reliability** | Task failure tolerance | Celery automatic exponential backoff (max 3 retries) |
