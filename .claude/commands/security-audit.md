---
description: Perform a deep security and hardening audit across the codebase.
---

Invoke the agent-skills:security-and-hardening skill alongside the specialist security-auditor persona (`.claude/agents/security-auditor.md`).

## Process

1. Check for hardcoded secrets, API tokens, or unprotected environment credentials.
2. Audit all public API endpoints in `apps/api` for input validation (Pydantic models) and SQL injection vulnerabilities.
3. Verify Next.js routes and Server Actions in `apps/web` for CSRF, XSS, and proper auth session validation.
4. Review CORS, Content Security Policy, and HTTP security headers.
5. Cross-reference with the [security-checklist.md](.claude/references/security-checklist.md).
6. Provide severity-ranked findings with concrete remediations.
