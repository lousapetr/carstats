---
name: code-review
description: Structured code review following team standards. Use when reviewing code or checking PRs.
---

Follow this structure:

### 1. Security (always first)
- SQL/NoSQL injection, unvalidated input, missing auth, secrets in code, CORS issues

### 2. Error Handling
- Async operations in try/catch, errors logged with context, consistent error format, no empty catch blocks

### 3. Performance
- N+1 queries, missing indexes, unbounded queries, large payloads without pagination

### 4. Code Quality
- Functions under 30 lines, no magic numbers, no `any` types, dead code removed

### 5. Testing
- Is this testable? Suggest specific test cases if none exist.

For each finding: **Severity** (CRITICAL/WARNING/SUGGESTION), **Location** (file:line), **Issue**, **Fix** (concrete suggested change, not just a description of the problem).

Order findings by severity, CRITICAL first. If there are no findings in a category, skip it rather than stating "no issues found."
