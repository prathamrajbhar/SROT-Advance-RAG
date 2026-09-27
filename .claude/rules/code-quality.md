# Code Quality, Modularity & Error Recovery Rules

Strict conventions governing all code modifications, refactorings, and reviews.

---

## 1. Code Cleanliness
- **File Length Limit**: No file should exceed 200 lines. If a file is approaching 200 lines, extract helper functions, types, sub-components, or custom hooks into dedicated files.
- **Early Returns**: Favor guard clauses and early returns over deeply nested `if/else` structures.
- **Clean Naming**: Use descriptive, intention-revealing variable and function names. Avoid ambiguous abbreviations like `data`, `res`, `temp`, `x`, `val`.
- **No Console Logging**: Never leave `console.log` in committed code. Use structured logger facilities or delete debug statements before committing.
- **No Dead Code**: Remove unused imports, dead functions, and obsolete commented-out blocks immediately.

---

## 2. Dependency Discipline
- **No Unsolicited Dependencies**: Never run `npm install <pkg>` or `pip install <pkg>` without explicit user consent. Always verify if the functionality can be cleanly implemented using built-in standard libraries or existing project dependencies.
- **Up-to-Date Versions**: When dependencies are required, consult the web for the latest stable, non-deprecated releases. Never rely on obsolete packages.

---

## 3. Systematic Debugging & Error Handling
- **Inspect Full Stack Traces**: Never make blind guesses about errors. Read the full traceback, identify the exact line of failure, and analyze the root cause.
- **Root-Cause Fixes**: Do not patch around symptoms (e.g., adding arbitrary null checks to mask uninitialized state). Fix the root state management or data contract issue.
- **Transparent Communication**: Whenever an error occurs, clearly state:
  1. What failed
  2. Why it failed
  3. What exact changes were made to fix it
