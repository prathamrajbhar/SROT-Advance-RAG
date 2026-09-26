# API Reference — SROT

Base URL: `https://{host}/api/v1` (dev: `http://localhost:8000/api/v1`)
Interactive docs: `GET /docs` (Swagger, auto-generated from FastAPI).
Backend AI dependencies: Provider-agnostic LLM/judge integration (Anthropic, Gemini, OpenAI, Groq, Ollama, vLLM), embeddings, cross-encoder reranker, faster-whisper. Object storage: AWS S3 (LocalStack in dev).

## 1. Conventions

| Convention | Detail |
|---|---|
| Auth | `Authorization: Bearer <access_token>` on all routes except register/login/refresh |
| IDs | UUIDv4 everywhere |
| Timestamps | ISO-8601 UTC (`2026-09-27T00:05:00Z`) |
| Pagination | `?page=1&page_size=20` → response includes `items[]`, `page`, `page_size`, `total` |
| Tracing | Every response carries `X-Trace-Id`; frontend must surface it on error UI |
| Rate limits | `429` + `Retry-After` header; limits per security.md §9 (auth 5/min, upload 20/h, chat 60/h, eval 5/day) |
| Cost fields | `cost_usd` = real-time pricing calculation based on token counts or infrastructure time |

### Error envelope (RFC 7807 style)

```json
{
  "type": "https://srot.dev/errors/insufficient-permissions",
  "title": "Insufficient permissions",
  "status": 403,
  "detail": "Role 'viewer' cannot delete documents in this project.",
  "trace_id": "01J5KQ7D3XG2F9V8T6M4R0Y3PZ"
}
```

| Code | Meaning |
|---|---|
| 400 | Validation failed (detail names the field) |
| 401 | Missing/expired token |
| 403 | Authenticated but wrong role/project |
| 404 | Resource not found **in your scope** (never leaks cross-project existence) |
| 409 | Conflict (duplicate content hash, email taken) |
| 413 | File exceeds per-type size limit |
| 415 | Unsupported or mismatched MIME type |
| 422 | Malicious scan rejection (`error_code: SCAN_REJECTED`) |
| 429 | Rate limited |
| 503 | Dependency/Provider down; `detail` names it: `llm_provider`, `embedder`, `reranker`, `whisper`, `qdrant`, `s3` |

---

## 2. Auth

### POST /auth/register
```json
Request:  { "email": "a@b.com", "password": "min-12-chars", "full_name": "Asha" }
201: { "user": { "id": "uuid", "email": "a@b.com", "full_name": "Asha" },
       "access_token": "jwt", "expires_in": 900 }
```
Refresh token is set as httpOnly cookie (`refresh_token`, 7d, rotating).

### POST /auth/login
Identical response shape to register. `401` with generic message on bad credentials (no enumeration).

### POST /auth/refresh
Reads httpOnly cookie, rotates it (reuse revokes the family). Returns a new `access_token`.

### POST /auth/logout
Revokes refresh family, clears cookie. `204`.

---

## 3. Projects

### GET /projects
```json
200: { "items": [{ "id": "uuid", "name": "Client A", "description": "...",
                   "role": "owner", "document_count": 6,
                   "updated_at": "2026-09-27T00:00:00Z" }],
       "page": 1, "page_size": 20, "total": 2 }
```

### POST /projects
```json
Request:  { "name": "Client A", "description": "optional" }
201: { "id": "uuid", "name": "Client A", "created_at": "2026-09-27T00:00:00Z" }
```

### GET /projects/{project_id}
`200` with project + aggregate stats:
```json
{ "id": "uuid", "name": "Client A", "document_count": 6, "indexed_count": 5,
  "failed_count": 1, "total_chunks": 812, "last_indexed_at": "..." }
```
404-style "not in your scope" for non-members.

### PATCH /projects/{project_id}
`{ "name": "...", "description": "..." }` — owner/editor only.

### DELETE /projects/{project_id}
Owner only. Cascades: S3 prefix `projects/{pid}/`, Qdrant collection, chunks, conversations. `204`. Emits audit event.

---

## 4. Project Members

| Method | Path | Body | Notes |
|---|---|---|---|
| GET | /projects/{id}/members | — | `[{ user: {id, email, full_name}, role, joined_at }]` |
| POST | /projects/{id}/members | `{ "email": "...", "role": "editor\|viewer" }` | owner only |
| PATCH | /projects/{id}/members/{user_id} | `{ "role": "viewer" }` | owner only; cannot change own role |
| DELETE | /projects/{id}/members/{user_id} | — | owner only; `403` on removing last owner |

---

## 5. Documents

### POST /projects/{id}/documents  (upload)

`multipart/form-data`, field `files` (multiple allowed). Limits by MIME class per security.md §6.

```json
202: { "uploads": [
  { "document_id": "uuid", "filename": "report.pdf", "sha256": "...",
    "status": "queued", "duplicate": false },
  { "filename": "report.pdf", "duplicate": true, "existing_document_id": "uuid",
    "note": "Identical content already indexed as v1" }
] }
```

### GET /projects/{id}/documents
Query params: `status=indexed|failed|...`, `q=<filename search>`, pagination.
```json
200: { "items": [{ "id": "uuid", "filename": "report.pdf", "mime_type": "application/pdf",
                   "size_bytes": 204800, "status": "indexed",
                   "stats": { "pages": 42, "chunk_count": 138, "token_count": 38900 },
                   "pii_flags": { "density": "low", "kinds": ["email"] },
                   "error_code": null, "error_human": null,
                   "created_at": "...", "indexed_at": "..." }] }
```

### GET /projects/{id}/documents/{doc_id}/status
```json
200: { "status": "embedding", "progress_pct": 64, "stage_detail": "312/480 chunks embedded" }
```

### GET /projects/{id}/documents/{doc_id}/content
```json
200: { "url": "<presigned S3 GET URL>", "expires_in": 300 }
```
Viewer deep-linking: frontend appends `&page=7` or `&t=184` hints; never proxies bytes through the API.

### POST /projects/{id}/documents/{doc_id}/retry
Only valid when `status=failed`. Re-enqueues ingestion. `202`.

### DELETE /projects/{id}/documents/{doc_id}
Editor/owner. Removes S3 object, Qdrant points, chunk rows. `204`. Emits audit event.

---

## 6. Conversations

### GET /projects/{id}/conversations
List with `title` (auto-generated from first query after 2nd turn), `message_count`, `updated_at`.

### POST /projects/{id}/conversations
`{ "title": "optional" }` → `201 { "id": "uuid" }`.

### GET /conversations/{conv_id}/messages
```json
200: { "items": [
  { "id": "uuid", "role": "user", "content_md": "What is the payment term?", "created_at": "..." },
  { "id": "uuid", "role": "assistant", "content_md": "The payment term is Net-30 [1]...",
    "verdict": "answered", "confidence": 0.83, "faithfulness": 0.92,
    "latency_ms": 1150, "cost_usd": 0.00042,
    "model_provider": "gemini", "model_name": "gemini-2.0-flash",
    "citations": [{ "chunk_id": "uuid", "document_id": "uuid",
                    "document_name": "msa.pdf",
                    "locator": { "page_number": 7 },
                    "snippet": "…payment terms: Net-30 from invoice date…" }] }
] }
```
Audio/video citations carry `"locator": { "start_s": 184.2, "end_s": 209.5 }`; Excel rows carry `{ "row_range": [41, 52], "sheet": "LineItems" }`.

### DELETE /conversations/{conv_id}
`204`.

---

## 7. Chat (the core endpoint)

### POST /conversations/{conv_id}/messages — SSE stream

Request:
```json
{ "content": "What are the payment terms and any penalties for late payment?",
  "debug": false }
```

Response `text/event-stream`. Event sequence:
```
event: status    data: {"stage": "retrieving"}
event: status    data: {"stage": "reranking"}
event: status    data: {"stage": "generating", "provider": "gemini", "model": "gemini-2.0-flash"}
event: token     data: {"t": "The "}
event: token     data: {"t": "payment term is Net-30"}
event: token     data: {"t": " [1]. "}
...
event: citation  data: {"index": 1, "chunk_id": "uuid", "document_id": "uuid",
                        "document_name": "msa.pdf", "locator": {"page_number": 7},
                        "snippet": "…"}
event: status    data: {"stage": "verifying"}
event: final     data: {"message_id": "uuid", "verdict": "answered",
                        "confidence": 0.83, "faithfulness": 0.92,
                        "coverage": 0.9, "top_rerank_score": 0.78,
                        "latency_ms": 1150, "prompt_tokens": 2300,
                        "completion_tokens": 210, "cost_usd": 0.00042,
                        "model_provider": "gemini", "model_name": "gemini-2.0-flash"}
```

Insufficiency case (no `token` events ever stream):
```
event: status  data: {"stage": "retrieving"}
event: final   data: {"verdict": "insufficient_evidence", "confidence": 0.31,
                      "searched_documents": [{"document_id":"uuid","filename":"msa.pdf"}],
                      "content_md": "I don't have enough evidence in this project's documents to answer that."}
```

With `debug: true` (owner/editor only), an extra event precedes `final`:
```
event: retrieval  data: {"bm25_ids": [...], "dense_ids": [...], "fused_ids": [...],
                         "reranked": [{"chunk_id": "...", "score": 0.78}]}
```

Mid-stream errors:
```
event: error  data: {"code": "PROVIDER_RATE_LIMIT", "message": "Upstream LLM provider rate limit exceeded.",
                     "retryable": true, "retry_after_s": 10, "trace_id": "..."}
```
Other error codes: `PROVIDER_AUTH_FAILED`, `PROVIDER_UNAVAILABLE`, `EMBEDDER_UNAVAILABLE`, `RERANKER_UNAVAILABLE`, `QDRANT_UNAVAILABLE`.

Client rules (from rules.md): render tokens only from real stream data; never fabricate citations from `citation` events that never arrived; show the verdict pill + confidence dial from `final`.

---

## 8. Evaluation

### POST /projects/{id}/eval/run
Owner/editor. Body: `{ "notes": "optional" }` → `202 { "eval_run_id": "uuid" }`. Async; poll the list endpoint. Judge = configured LLM provider.

### GET /projects/{id}/eval/runs
```json
200: { "items": [{ "id": "uuid", "status": "completed", "triggered_by": "uuid",
                   "model_provider": "gemini", "model_name": "gemini-2.0-flash",
                   "faithfulness": 0.93, "context_precision": 0.84,
                   "context_recall": 0.81, "answer_relevancy": 0.9,
                   "question_count": 12, "created_at": "..." }] }
```

### GET /projects/{id}/eval/runs/{run_id}
Adds `report_json`: per-question rows `{question, expected, actual, faithfulness, verdict, latency_ms}` — powers the metrics dashboard.

---

## 9. Admin, Metrics & Health

| Method | Path | Purpose |
|---|---|---|
| GET | /projects/{id}/metrics | Dashboard aggregates: chat volume, avg/p95 latency, avg faithfulness, verdict distribution, daily cost breakdown, ingest failures by error code |
| GET | /projects/{id}/audit | Paginated audit events (owner only) |
| GET | /health | Liveness — always 200 |
| GET | /ready | Readiness `200/503`: names status of `pg, redis, qdrant, s3, llm_provider, embedder, reranker, whisper` individually |

`/ready` sample:
```json
{ "ready": true,
  "checks": { "pg": "ok", "redis": "ok", "qdrant": "ok", "s3": "ok",
              "llm_provider": "ok (gemini: gemini-2.0-flash)",
              "embedder": "ok", "reranker": "ok", "whisper": "ok" } }
```

---

## 10. Endpoint × Role Matrix (must match security.md §3)

| Endpoint group | viewer | editor | owner |
|---|---|---|---|
| Chat, list docs/conversations, presigned content | ✓ | ✓ | ✓ |
| Upload/retry/delete documents | ✗ | ✓ | ✓ |
| Eval trigger, members, audit, project delete | ✗ | eval only | ✓ |
