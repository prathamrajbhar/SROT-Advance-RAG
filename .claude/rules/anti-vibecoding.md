# Production Engineering Standards (Anti-Vibe-Coding Rules)

"Vibe coding" (blindly accepting AI-generated drafts because they run once on localhost) causes silent bugs, catastrophic performance leaks, and unmaintainable black boxes. Every AI action in this repository must operate as a **Staff Software Engineer**, never an unchecked typist.

---

## 1. Eliminate the "Localhost Mirage"
- **Scale-Aware Queries**: Never generate unrestricted `SELECT *` or unbound ORM queries. Always require pagination (`limit`, `offset` / keyset), explicit indices, and selective column projection.
- **Solve $N+1$ Problems**: When querying relational entities in SQLAlchemy or Prisma/Drizzle, explicitly use joined/select-in loading. Never load related entities inside a loop.
- **Connection & Resource Hygiene**: Database connections, HTTP client sessions (`httpx.AsyncClient`), file descriptors, and stream handles must be managed via async context managers (`async with`). Never leave dangling connections.
- **Concurrency & Race Conditions**: Protect shared state and database writes with optimistic concurrency, row locks, or idempotency keys where duplicates can occur.

---

## 2. Zero-Trust Security Gates
- **Input Validation at the Edge**: Every public route in FastAPI must validate inputs with Pydantic v2 schemas. Every Next.js Server Action or route handler must validate inputs with Zod. Never trust client payload types.
- **No Insecure Dynamic Code**: Zero dynamic SQL concatenation or unescaped template interpolation. Always use parameterized queries.
- **Credential & Secret Protection**: Never hardcode secrets, tokens, salts, or passwords in files or tests. Always retrieve from environment variables validated at startup via `pydantic-settings` or env schemas.
- **Strict Authorization**: Never assume user authentication implies authorization. Always verify object-level ownership / tenant tenancy before returning or modifying records.

---

## 3. Anti-Black-Box & Architecture Preservation
- **No Blind Rewrites**: Never rewrite an entire working file when a targeted edit solves the issue. Understand the existing codebase before modifying it.
- **Preserve Documentation & Contracts**: Maintain existing docstrings, OpenAPI schemas, and TypeScript interfaces unless the spec explicitly dictates a breaking change.
- **Chesterton's Fence**: If code appears redundant or unusual, determine *why* it was written before deleting or refactoring it.
- **Single Responsibility Principle**: One function does one thing. Keep files concise (under 200 lines). Break complex workflows into modular services, repositories, and hooks.

---

## 4. Verification Over Hallucination
- ** Beyonce Rule**: "If you liked it, then you should have put a test on it." Code is not finished because it looks plausible or typed cleanly. It must have automated tests proving:
  1. The happy path works.
  2. Edge cases (null inputs, empty lists, invalid formats) fail gracefully.
  3. Errors return standard HTTP error status codes (400, 401, 403, 404, 422, 500).
- **Run Verification Commands**: Always verify with `npm run typecheck`, pytest, and linting. Never report a task complete without having executed tests.
- **Never Swallow Errors**: Do not write empty `except:` or `catch (e) {}` blocks. Log structured errors and re-throw or return domain-specific error results.
