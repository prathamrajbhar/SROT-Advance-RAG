# Screen Specifications & UI Wireframes

## Project: SROT (Advanced Multimodal Enterprise RAG)
**Document Version:** 1.1.0  
**Status:** Approved for Agile Execution  
**Theme:** Strict Enterprise Light  

---

## 1. Screen Inventory & Route Map

```
/
├── /onboarding                   # Screen 1: 5-Step SaaS Onboarding, BYOK & Sample Data Seeder
├── /workspace/:id/documents      # Screen 2: Data Catalog, S3 Multipart Dropzone & SSE Progress Stream
├── /workspace/:id/chat           # Screen 3: Analytical Split-View Chat & Multimodal Inspector (Bounding Box Overlay)
├── /workspace/:id/settings       # Screen 4: BYOK Key Vault & Storage Configuration
└── /workspace/:id/analytics      # Screen 5: Ragas Benchmark & Observability Dashboard
```

---

## 2. Screen 1: SaaS Onboarding Wizard (`/onboarding`)

### 2.1 Purpose & User Flow
New organization administrators create their workspace, select their AI model provider (Cloud API vs. Self-Hosted Local Ollama/vLLM) with real-time connection verification, and optionally seed a verified enterprise sample pack with one click.

### 2.2 Wireframe (Step 2 & Step 5)
```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  SROT Enterprise                                                  Logged in as: admin@co │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                               WORKSPACE SETUP WIZARD                                     │
│     [1. Workspace] ─── [2. Provider Mode] ─── [3. Credentials] ─── [4. S3] ─── (5. Done) │
│                                                                                          │
│   ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│   │ Step 5: Workspace Ready to Launch                                                │   │
│   │ Your AES-256 encrypted provider connection is healthy and verified.             │   │
│   │                                                                                  │   │
│   │ ┌──────────────────────────────────────────────────────────────────────────────┐ │   │
│   │ │ [★] Load Enterprise Sample Dataset (Recommended for First-Time Users)        │ │   │
│   │ │                                                                              │ │   │
│   │ │ Instantly provisions a verified multi-modal pack to your workspace:         │ │   │
│   │ │ • sample_financials.xlsx (P&L sheets with DuckDB SQL ready)                 │ │   │
│   │ │ • sample_contract.pdf (Multi-column document with tables & bounding boxes)  │ │   │
│   │ │ • sample_tech_demo.mp4 (30-second video with timestamped transcript)         │ │   │
│   │ │ • sample_audio_brief.mp3 (Spoken voice memo with speaker markers)            │ │   │
│   │ │                                                                              │ │   │
│   │ │ [ Load Sample Pack & Start Exploring (10s) ]                                 │ │   │
│   │ └──────────────────────────────────────────────────────────────────────────────┘ │   │
│   │                                                                                  │   │
│   │ Or skip sample data to upload your own corporate files immediately.              │   │
│   │                                                                                  │   │
│   │ ──────────────────────────────────────────────────────────────────────────────── │   │
│   │ [ Back ]                                                    [ Go to Dashboard ->] │   │
│   └──────────────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Screen 2: Workspace Data Catalog, S3 Multipart Upload & SSE (`/workspace/:id/documents`)

### 3.1 Purpose & S3 Multipart Architecture
Handles multi-gigabyte uploads directly to AWS S3 using parallel chunk parts, displays real-time progress via Server-Sent Events (SSE) from Redis, and provides modal filtering.

### 3.2 Wireframe (ASCII)
```
┌─────────────────┬────────────────────────────────────────────────────────────────────────┐
│ SROT Enterprise │ Documents / Ingestion Catalog                       [ + Upload Files ] │
├─────────────────┼────────────────────────────────────────────────────────────────────────┤
│ [Workspace: AI] │ ┌────────────────────────────────────────────────────────────────────┐ │
│                 │ │  Drag & drop PDF, DOCX, XLSX, MP4, MP3, PNG files here             │ │
│ • Documents     │ │  Files > 50MB use S3 Parallel Multipart Upload (Chunk size: 10MB)  │ │
│ • Chat          │ └────────────────────────────────────────────────────────────────────┘ │
│ • Analytics     │                                                                        │
│ • Settings      │ Active Uploads (Direct-to-S3):                                         │
│                 │ ┌────────────────────────────────────────────────────────────────────┐ │
│                 │ │ product_keynote.mp4 (450 MB)                                       │ │
│                 │ │ Parts: [████████████████░░░░░░░░] 65% (4 parts in parallel)         │ │
│                 │ └────────────────────────────────────────────────────────────────────┘ │
│                 │                                                                        │
│                 │ Filter: [All (24)] [PDF (12)] [Excel (5)] [Video (4)] [Audio (3)]      │
│                 │                                                                        │
│                 │ ┌────────────────────────────────────────────────────────────────────┐ │
│                 │ │ Document Name    │ Modality │ Size    │ Chunks │ Status  │ Actions │ │
│                 │ ├──────────────────┼──────────┼─────────┼────────┼─────────┼─────────┤ │
│                 │ │ Q3_Earnings.xlsx │ Tabular  │ 4.2 MB  │ 42     │ ● Ready │ [···]   │ │
│                 │ │ Tech_Talk.mp4    │ Video    │ 184 MB  │ 128    │ ● Ready │ [···]   │ │
│                 │ │ Legal_Terms.pdf  │ Document │ 12.8 MB │ 310    │ ◐ 72%   │ [···]   │ │
│                 │ │   └─ SSE: [Transcribing OCR pages: 8/12] (Live via Redis PubSub)   │ │
│                 │ └────────────────────────────────────────────────────────────────────┘ │
└─────────────────┴────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Component Breakdown
- **`S3MultipartDropzone.tsx`**: Manages chunk slicing (10MB parts), parallel PUT requests to S3 presigned URLs, and multipart completion.
- **`SseProgressBar.tsx`**: Uses `useEventSource` connected to `/api/v1/documents/:id/progress-stream`, rendering live stage messages without DB polling.
- **`DocumentTable.tsx`**: High-density table with sorting, modality filter tabs, and action dropdowns.

---

## 4. Screen 3: Analytical Split-View Chat & Multimodal Inspector (`/workspace/:id/chat`)

### 4.1 Purpose & Visual Bounding Box Grounding
Users submit questions; the system generates answers with clickable citations. Clicking a PDF citation opens the PDF Viewer tab, which automatically draws a translucent bounding box highlight over the exact source passage.

### 4.2 Wireframe (ASCII)
```
┌──────┬───────────────────────────────────────────┬───────────────────────────────────────┐
│ SROT │ Analytical Synthesis View                 │ Multimodal Source Inspector       [✕] │
├──────┼───────────────────────────────────────────┼───────────────────────────────────────┤
│ Nav  │ User:                                     │ [● PDF Page 14] [Video] [Audio] [SQL] │
│      │ "What are the termination clauses in the  │                                       │
│ Doc  │ supplier agreement regarding IP rights?"  │ Source: Master_Supplier_Agreement.pdf │
│      │                                           │ Page: 14 of 48                        │
│ Chat │ SROT Synthesizer:                         │ ┌───────────────────────────────────┐ │
│      │ Under Section 9.2, either party may       │ │  9. INTELLECTUAL PROPERTY RIGHTS  │ │
│ Sett │ terminate immediately if proprietary      │ │  9.1 Ownership of Background IP...│ │
│      │ code is disclosed without prior written   │ │ ┌───────────────────────────────┐ │ │
│      │ consent [PDF: Agreement.pdf, P.14].       │ │ │█ 9.2 Termination for IP Breach:│ │ │
│      │                                           │ │ │█ Either party may terminate   │ │ │
│      │ Financial penalties are outlined in       │ │ │█ immediately if proprietary   │ │ │
│      │ the liquidated damages schedule:          │ │ │█ code or confidential trade...│ │ │
│      │ [SQL: Schedule_B.xlsx, 2 Rows].           │ │ └───────────────────────────────┘ │ │
│      │                                           │ │  [Highlighted Bounding Box Overlay]│
│      │ ───────────────────────────────────────── │ └───────────────────────────────────┘ │
│      │ [ Ask an analytical question... ]  [Send] │ Normalized Box: [0.32, 0.12, 0.44, 0.88]
└──────┴───────────────────────────────────────────┴───────────────────────────────────────┘
```

### 4.3 Component Breakdown
- **`ChatContainer.tsx`**: Streaming response with inline citation badges.
- **`SplitInspectorDrawer.tsx`**: Slide-over drawer with 4 specialized tabs:
  - **`PdfViewerTab.tsx`**: Canvas PDF renderer using S3 presigned URL with dynamic canvas bounding box highlight overlay.
  - **`VideoPlayerTab.tsx`**: HTML5 player with programmatic `.currentTime` seek and visual keyframe preview.
  - **`AudioPlayerTab.tsx`**: Audio player with synchronized transcript.
  - **`SqlGridTab.tsx`**: Interactive DuckDB SQL table with query execution trace.

---

## 5. Screen 4 & Screen 5: Settings & Analytics

- **`/workspace/:id/settings`**: BYOK Key Vault with AES-256 encryption, connection testing, and S3 bucket health status.
- **`/workspace/:id/analytics`**: Real-time Ragas metrics (Faithfulness $\ge 95\%$, Context Precision $\ge 90\%$), query throughput, and Celery worker latency telemetry.
