# SROT Project — AI Agent Guidelines & Architecture

Welcome to the SROT monorepo. This repository delivers a production-grade full-stack system built with **Next.js 15 (App Router)** and **FastAPI**.

AI agents working in this repository operate under the discipline of senior staff software engineers. Unchecked "vibe coding" (blindly accepting unverified code, skipping tests, ignoring edge cases, or creating black-box abstractions) is prohibited.

---

## 1. Project Overview & Structure

```
SROT/
├── apps/
│   ├── api/                 # FastAPI backend (Python 3.11+, SQLAlchemy 2.0 Async, Alembic, Pydantic v2)
│   └── web/                 # Next.js 15 frontend (React 19, Tailwind CSS, TypeScript strict mode)
├── infra/                   # Infrastructure & deployment configuration
├── scripts/                 # Operational scripts (setup, health check)
└── .claude/                 # Claude Code configuration, rules, skills, and personas
    ├── commands/            # Slash command workflows (/spec, /plan, /build, /test, /review, /ship, etc.)
    ├── rules/               # Production quality gates, anti-vibecoding, and full-stack rules
    ├── skills/              # 25 production-grade engineering skills (from addyosmani/agent-skills)
    ├── references/          # Engineering checklists (DoD, security, webperf, testing, observability)
    └── agents/              # Specialist reviewer personas (security, performance, reviewer, test engineer)
```

---

## 2. Essential Commands

- **Setup project**: `npm run setup`
- **Start development (all)**: `npm run dev` (starts API on :8000 and Web on :3000 concurrently)
- **Start API only**: `npm run dev:api`
- **Start Web only**: `npm run dev:web`
- **Run API tests**: `npm run test` or `npm run test:api`
- **Run TypeScript check**: `npm run typecheck`
- **Apply DB migrations**: `npm run migrate`
- **Check service health**: `npm run health`

---

## 3. Core Engineering Rules & Boundaries

### Always
- Follow the skills in `.claude/skills/` during task execution.
- Validate ideas and requirements before jumping into code using `/spec` or `.claude/skills/spec-driven-development/`.
- Break complex tasks into verifiable units via `/plan` or `.claude/skills/planning-and-task-breakdown/`.
- Apply Test-Driven Development (TDD) — write tests demonstrating the need for change, then make them pass.
- Enforce strict typing (no `any` in TypeScript; full Pydantic v2 schemas in Python).
- Enforce file modularity: keep files under 200 lines; separate UI, hooks, and services.
- Run `npm run typecheck` and `npm run test:api` before reporting tasks complete.

### Never
- Never add new npm or pip packages without asking the user.
- Never rewrite working code when a surgical modification solves the requirement.
- Never write prototype-grade UI: all interactive elements need hover, focus, active, disabled, empty, and loading states.
- Never bypass database connection pooling, unbound queries, or omit pagination.
- Never commit `console.log` statements or silence errors with empty catch blocks.

---

## 4. Claude Code Workflows (Slash Commands)

- `/spec` — Clarify requirements, define scope, edge cases, and acceptance criteria.
- `/plan` — Generate an incremental implementation plan with clear checkpoints.
- `/build` — Implement tasks step-by-step with failing tests first, code, and verification.
- `/test` — Generate unit, integration, or regression tests against existing components.
- `/review` — Perform a rigorous code quality, readability, and architecture review.
- `/code-simplify` — Refactor complex logic, reduce cognitive load, and apply Chesterton's fence.
- `/security-audit` — Audit for OWASP top 10, auth holes, injection vulnerabilities, and secret leaks.
- `/ship` — Verify full Definition of Done, run pre-flight gates, and package changes cleanly.
