---
name: implement-feature
description: >
  Given a classified feature issue, decompose into steps, implement
  incrementally, write tests. Conservative — prefers smaller scope.
license: Apache-2.0
allowed-tools: [read, edit, write, task_tracker, codebase-grep, detect-conventions]
metadata:
  author: repo-surgeon
  version: 1.0.0
  category: feature-development
  risk_tier: medium
---

## Instructions

### 1. Decompose
Read the issue body carefully. Use `task_tracker` to create a checklist of steps:
- API/interface design
- Implementation
- Happy-path test
- Edge-case test
- Documentation update (if a public API)

For scope `L` features (per `classify-issue` output), STOP and request the issue be split. Comment with a proposed decomposition. Do not proceed.

### 2. Read for context
- Use `codebase-grep` to find related code (similar patterns, interfaces, tests).
- Read 3-5 files to understand: naming conventions, error handling style, test structure, where things live.
- Cross-reference with `memory/repos/<TARGET_REPO>/conventions.md`.

### 3. Design before coding
In your reasoning, sketch:
- The interface (function signatures, types, where they live)
- The implementation approach (which existing utilities to reuse)
- The test strategy

Briefly summarize in the PR body's `## What changed` section.

### 4. Implement incrementally
- Add the new function/module skeleton first.
- Add the happy-path test (it should fail).
- Implement until it passes.
- Add edge-case tests one at a time.
- Implement until all pass.

Use `task_tracker` to mark items complete as you go.

### 5. Run the full test suite
Via `run-tests` with `scope: all`. Must pass.

### 6. Update memory if non-obvious
- If you introduced a new utility that others should reuse, add to `memory/repos/<TARGET_REPO>/conventions.md` via `CONVENTION:` sentinel.
- If the feature implementation revealed a hidden constraint, emit `LESSON:`.

## Output Format

```json
{
  "issue_number": int,
  "files_added": ["path/to/new/file"],
  "files_modified": ["path/to/existing/file"],
  "tests_added": ["path:line"],
  "lines_added": int,
  "lines_removed": int,
  "approach_summary": "2-3 sentence design summary",
  "tests_pass": boolean,
  "security_sensitive": boolean,
  "approval_required": boolean
}
```

## Notes

- For ANY feature, set `approval_required: true` — features get a human-approval gate in the workflow before PR is opened. This is intentional friction.
- Features under 50 LOC can sometimes be auto-approved if `RULES-override.md` allows it.
- Never invent new top-level dependencies. If you need a library, comment on the issue asking for approval first.
- If the feature touches auth/security, set `security_sensitive: true`.
