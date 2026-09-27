# Workspace Rules: Next.js 15 App Router & FastAPI Monorepo

This monorepo consists of:
- `apps/web`: Next.js 15 (React 19, Tailwind CSS, Lucide React, TypeScript strict mode)
- `apps/api`: FastAPI (Python 3.11+, Pydantic v2, SQLAlchemy 2.0 Async, Alembic, asyncpg)

---

## 1. Next.js 15 (`apps/web`) Standards
- **Server Components by Default**: Default to React Server Components (RSC). Only add `"use client"` when component requires client interactivity (`useState`, `useEffect`, event listeners, browser APIs).
- **Asynchronous Params/SearchParam Access**: Next.js 15 requires awaiting `params` and `searchParams` in Page and Layout components:
  ```typescript
  type Props = { params: Promise<{ id: string }> };
  export default async function Page({ params }: Props) {
    const { id } = await params;
    // ...
  }
  ```
- **Type Safety**:
  - No `any` type under any circumstance. Use generics, unknown with type guards, or explicit interfaces.
  - Keep components modular: one component per file, under 200 lines.
  - Co-locate UI logic into `components/`, reusable state hooks into `hooks/`, and data fetchers into `lib/` or `services/`.
- **Styling & Accessibility**:
  - Use Tailwind CSS with `tailwind-merge` and `clsx`.
  - Dark mode support by default.
  - Interactive elements must implement clear focus, hover, active, and disabled states.
  - Provide accessible labels (`aria-label`, `<label>`) and keyboard navigation support.

---

## 2. FastAPI (`apps/api`) Standards
- **Async Endpoints**: Every I/O-bound endpoint must be `async def`.
- **Pydantic v2 Models**:
  - Use `model_config = ConfigDict(...)` instead of nested `class Config`.
  - Separate `CreateSchema`, `UpdateSchema`, and `ResponseSchema` (`from_attributes = True`).
- **SQLAlchemy 2.0 Async**:
  - Always use `select(...)` 2.0 syntax.
  - Always use `AsyncSession` injected via FastAPI dependency:
    ```python
    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as session:
            yield session
    ```
  - Ensure transactions are properly committed or rolled back automatically via context managers.
- **Alembic Migrations**:
  - Never alter production tables manually; always generate and inspect an Alembic migration (`alembic revision --autogenerate`).

---

## 3. Monorepo Workflow Commands
- Setup: `npm run setup`
- Dev mode: `npm run dev` (runs both `api` and `web` concurrently)
- Test API: `npm run test` or `npm run test:api`
- Typecheck frontend: `npm run typecheck`
- Health check: `npm run health`
- Database migration: `npm run migrate`
