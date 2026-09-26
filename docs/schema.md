# Schema — Data Model, Vector Schema & Configuration

## 1. Postgres Schema (Alembic-managed)

```sql
-- ──────────────────────────── AUTH ────────────────────────────
create table users (
  id            uuid primary key default gen_random_uuid(),
  email         citext unique not null,
  password_hash text not null,
  full_name     text,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create table refresh_tokens (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references users(id) on delete cascade,
  token_hash text not null,
  family_id  uuid not null,
  expires_at timestamptz not null,
  revoked_at timestamptz,
  created_at timestamptz not null default now()
);

-- ──────────────────────────── PROJECTS ────────────────────────
create table projects (
  id          uuid primary key default gen_random_uuid(),
  owner_id    uuid not null references users(id),
  name        text not null,
  description text,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create type project_role as enum ('owner', 'editor', 'viewer');

create table project_members (
  project_id uuid not null references projects(id) on delete cascade,
  user_id    uuid not null references users(id) on delete cascade,
  role       project_role not null,
  created_at timestamptz not null default now(),
  primary key (project_id, user_id)
);

-- ──────────────────────────── DOCUMENTS ───────────────────────
create type ingest_status as enum
  ('queued','parsing','chunking','embedding','indexing','indexed','failed');

create table documents (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid not null references projects(id) on delete cascade,
  uploaded_by uuid not null references users(id),
  filename    text not null,
  mime_type   text not null,
  size_bytes  bigint not null,
  sha256      text not null,
  s3_key      text not null,     -- projects/{pid}/docs/{sha256}/v{n}, AWS S3 only
  status      ingest_status not null default 'queued',
  error_code  text,          -- 'CORRUPT_PDF','UNSUPPORTED_MIME','SCAN_REJECTED',...
  error_human text,          -- user-facing message from the same event
  stats       jsonb,         -- { pages, duration_s, rows, chunk_count, token_count }
  pii_flags   jsonb,         -- { density, kinds[] }
  version     int  not null default 1,
  created_at  timestamptz not null default now(),
  indexed_at  timestamptz,
  unique (project_id, sha256, version)
);
create index documents_project_idx on documents(project_id, status);

-- ──────────────────────────── CHUNKS ──────────────────────────
create table chunks (
  id             uuid primary key default gen_random_uuid(),
  document_id    uuid not null references documents(id) on delete cascade,
  project_id     uuid not null references projects(id) on delete cascade,
  chunk_index    int not null,
  parent_id      uuid references chunks(id) on delete cascade,
  kind           text not null,   -- 'text','table_row','heading','transcript_segment'
  token_count    int not null,
  content        text not null,
  locator        jsonb,           -- {page_number} | {start_s,end_s} | {row_range:[a,b],sheet}
  content_hash   text not null,
  embedding_id   uuid,            -- point id in Qdrant
  ftsv           tsvector generated always as
                 (to_tsvector('english', content)) stored
);
create index chunks_doc_idx     on chunks(document_id, chunk_index);
create index chunks_project_fts on chunks using gin(ftsv);
create index chunks_parent_idx  on chunks(parent_id);

-- ──────────────────────────── CHAT ────────────────────────────
create type verdict as enum ('answered','insufficient_evidence','unverified','error');

create table conversations (
  id         uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects(id) on delete cascade,
  user_id    uuid not null references users(id),
  title      text,
  created_at timestamptz not null default now()
);

create table messages (
  id              uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references conversations(id) on delete cascade,
  role            text not null check (role in ('user','assistant','system')),
  content_md      text not null,
  created_at      timestamptz not null default now()
);

create table assistant_turns (
  message_id        uuid primary key references messages(id) on delete cascade,
  verdict           verdict not null,
  confidence        numeric(3,2),
  faithfulness      numeric(3,2),
  top_rerank_score  numeric(3,2),
  coverage          numeric(3,2),
  latency_ms        int,
  prompt_tokens     int,
  completion_tokens int,
  cost_usd          numeric(10,6),  -- accurately calculated token or compute cost
  model_provider    text not null,  -- 'anthropic','gemini','openai','groq','ollama','vllm'
  model_name        text not null,  -- e.g. 'claude-3-5-sonnet-20241022','gpt-4o-mini'
  retrieval         jsonb,          -- {bm25_ids[], dense_ids[], fused_ids[], reranked[{id,score}]}
  citations         jsonb           -- [{chunk_id, document_id, locator, snippet}]
);

-- ──────────────────────────── AUDIT & EVAL ────────────────────
create table audit_events (
  id          uuid primary key default gen_random_uuid(),
  actor_id    uuid,
  project_id  uuid,
  action      text not null,
  object_type text,
  object_id   uuid,
  ip          inet,
  user_agent  text,
  result      text not null,
  created_at  timestamptz not null default now()
);

create table eval_runs (
  id                uuid primary key default gen_random_uuid(),
  project_id        uuid not null references projects(id) on delete cascade,
  triggered_by      uuid references users(id),
  status            text not null,
  model_provider    text not null,
  model_name        text not null,
  faithfulness      numeric(3,2),
  context_precision numeric(3,2),
  context_recall    numeric(3,2),
  answer_relevancy  numeric(3,2),
  question_count    int,
  report_json       jsonb,
  created_at        timestamptz not null default now()
);
```

## 2. Qdrant Schema

One collection per project: `proj_<project_id>`.

**Vectors:** Configurable dimension (default 1024-dim for `bge-large-en-v1.5`, 1536 for OpenAI `text-embedding-3-small`, 768 for Gemini), cosine distance.

**Payload per point:**

| Field | Type | Notes |
|---|---|---|
| project_id | keyword | indexed, required, matches session |
| document_id | keyword | indexed |
| chunk_id | keyword | = chunks.id |
| parent_id | keyword | parent chunk UUID |
| kind | keyword | text / table_row / heading / transcript_segment |
| locator.page_number | integer | optional |
| locator.start_s / end_s | float | optional |
| locator.row_range | integer[] | optional, with sheet name in chunk metadata |
| pii | bool | indexed |
| content_hash | keyword | idempotent upserts |

**Sparse retrieval** lives in Postgres FTS (`chunks.ftsv`), not Qdrant sparse vectors — keeps retrieval code simple and debuggable. Scores from both sides are fused with RRF (architecture.md §4.4).

## 3. Redis Key Conventions

```
ratelimit:user:{id}:{endpoint_bucket}   TTL ~60s
conv:{id}:last_turns                    list, last 6 messages, TTL 24h
chat:{conv_id}:lock                     short lock to prevent double-submit
ingest:job:{doc_id}:progress            hash {stage, pct, worker}
trace:{request_id}                      ephemeral, TTL 1h
```

## 4. Configuration Schema (`pydantic-settings`)

All settings load from `.env` or system environment. Boot validation verifies presence of required variables for the chosen provider.

### Core & Infrastructure (Required)
| Variable | Purpose | Example |
|---|---|---|
| DATABASE_URL | Postgres DSN | `postgresql+asyncpg://user:pass@localhost:5432/srot` |
| REDIS_URL | Queue / cache / locks | `redis://localhost:6379/0` |
| QDRANT_URL | Vector DB | `http://localhost:6333` |
| S3_ENDPOINT_URL | AWS S3 or LocalStack URL | `http://localhost:4566` (dev) / `https://s3.us-east-1.amazonaws.com` |
| S3_REGION | AWS Region | `us-east-1` |
| S3_BUCKET | Storage bucket name | `srot-storage` |
| S3_ACCESS_KEY | AWS Access Key | `test` |
| S3_SECRET_KEY | AWS Secret Key | `test` |
| SECRET_KEY | JWT signing secret | `secret_32_chars_min` |

### LLM & Provider Configuration (.env swappable)
| Variable | Purpose | Options / Defaults |
|---|---|---|
| `LLM_PROVIDER` | Active LLM backend | `ollama` \| `openai` \| `anthropic` \| `gemini` \| `groq` \| `vllm` |
| `LLM_MODEL` | Target model name | e.g. `claude-3-5-sonnet-20241022`, `gemini-2.0-flash`, `gpt-4o-mini`, `llama3.1:8b` |
| `LLM_BASE_URL` | Base URL (for Ollama, vLLM, custom OpenAI proxies) | e.g. `http://localhost:11434/v1` |
| `ANTHROPIC_API_KEY` | API Key for Anthropic Claude | `sk-ant-...` (required if LLM_PROVIDER=anthropic) |
| `GEMINI_API_KEY` | API Key for Google Gemini | `AIzaSy...` (required if LLM_PROVIDER=gemini) |
| `OPENAI_API_KEY` | API Key for OpenAI | `sk-proj-...` (required if LLM_PROVIDER=openai) |
| `GROQ_API_KEY` | API Key for Groq Cloud | `gsk_...` (required if LLM_PROVIDER=groq) |

### Embedding & Reranking Services
| Variable | Purpose | Options / Defaults |
|---|---|---|
| `EMBEDDING_PROVIDER` | Embedding backend | `local` (default bge-large-en-v1.5) \| `openai` \| `gemini` \| `voyage` |
| `EMBEDDER_URL` | URL for local embedder container | `http://localhost:8001` |
| `RERANKER_PROVIDER` | Cross-encoder backend | `local` (default bge-reranker-v2-m3) \| `cohere` \| `jina` |
| `RERANKER_URL` | URL for local reranker container | `http://localhost:8002` |
| `WHISPER_URL` | URL for faster-whisper container | `http://localhost:8003` |
| `INTERNAL_MODEL_TOKEN` | Shared secret for private model containers | `internal_secret` |

### Tracing & Evaluation
| Variable | Purpose | Example |
|---|---|---|
| `LANGFUSE_HOST` | Self-hosted Langfuse host | `http://localhost:3001` |
| `LANGFUSE_PUBLIC_KEY` | Langfuse public key | `pk-lf-...` |
| `LANGFUSE_SECRET_KEY` | Langfuse secret key | `sk-lf-...` |

### Optional Tuning Defaults
`RERANK_MIN_SCORE=0.35`, `CHUNK_CHILD_TOKENS=250`, `CHUNK_PARENT_TOKENS=1500`, `HYBRID_TOP_K=40`, `LLM_TOP_K_PARENTS=8`, `RATE_LIMIT_CHAT_PER_HOUR=60`.

## 5. CI Invariants

- `apps/api/core/config.py` is the only place env vars are read.
- Every `.env.example` change = PR reviewer checklist hit.
- Alembic auto-check: migration head must match models (CI).
- Secrets security scan: CI blocks any committed plaintext secrets or API keys.
