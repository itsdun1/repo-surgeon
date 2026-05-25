---
name: fix-from-issue
description: >
  Given a classified bug issue, reproduce it, write a failing test, implement
  the fix, confirm the test passes. The most-used skill.
license: Apache-2.0
allowed-tools: [read, edit, write, cli, read-issue, run-tests, codebase-grep]
metadata:
  author: repo-surgeon
  version: 1.0.0
  category: bug-fixing
  risk_tier: medium
---

## Instructions

This skill follows a strict 6-step process. Do not skip steps.

### 1. Re-read the issue
The `read-issue` tool was already called by `classify-issue`. Use the issue body as your spec.

### 2. Locate the bug
- Use `codebase-grep` to find code that matches the issue's symptoms (function names, error messages, file paths mentioned).
- Read 2-3 candidate files fully.
- Form a hypothesis about which line(s) are wrong.

### 3. Write a FAILING test first (RULE 14)
- Detect the test framework from `memory/repos/<TARGET_REPO>/conventions.md` (or use `detect-conventions` if missing).
- Add a test that:
  - Reproduces the bug from the issue
  - Asserts the *correct* behavior (the test should currently FAIL because the code is buggy)
  - Has a descriptive name that references the issue: `test_cart_total_handles_decimal_prices_issue_142`
- Run the test via `run-tests` tool with `scope: file`. Confirm it FAILS.
- If the test passes immediately, your hypothesis is wrong. Go back to step 2.

### 4. Implement the fix
- Make the smallest change that turns the failing test green.
- Touch only the file(s) directly relevant to the bug.
- Do NOT refactor surrounding code (that's a separate PR).

### 5. Confirm the test now passes
- Run the test via `run-tests` again. Must pass.
- Also run the broader test suite via `run-tests` with `scope: all` — must not break other tests.
- If other tests break, your fix has unintended consequences. Revert and reconsider.

### 6. Emit learnings
- If the bug surfaced a non-obvious convention (e.g., "always use Money class, never raw numbers"), emit a `CONVENTION:` sentinel line.
- If the bug was hard to find, emit a `LESSON:` line describing what to look for next time.

## Output Format

```json
{
  "issue_number": int,
  "files_modified": ["path/to/file"],
  "test_added": "path/to/test/file:line",
  "lines_added": int,
  "lines_removed": int,
  "test_before_fix": "fail",
  "test_after_fix": "pass",
  "broader_suite_after_fix": "pass | fail",
  "diff_summary": "1-2 sentence explanation",
  "security_sensitive": boolean
}
```

## Notes

- If you cannot reproduce the bug after 3 grep attempts, ask in the issue comment for repro steps rather than guessing.
- If the fix would require modifying a forbidden path (migrations, secrets, etc.), abort and comment explaining what manual change is needed.
- Set `security_sensitive: true` if the diff touches auth/crypto/HTTP routes — this triggers the `security-reviewer` sub-agent in the workflow.
