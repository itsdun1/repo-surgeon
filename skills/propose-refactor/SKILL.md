---
name: propose-refactor
description: >
  Given a ranked smell backlog, pick the top smell and draft a minimal, safe
  refactor diff. Justify the change. Designed for low-risk wins.
license: Apache-2.0
allowed-tools: [read, edit, codebase-grep]
metadata:
  author: repo-surgeon
  version: 1.0.0
  category: refactoring
  risk_tier: low
---

## Instructions

1. Take the `candidates` output from `scan-for-smells` as input.
2. Filter:
   - Skip `status: persistent` items already in 3+ prior scans (they're blocked on something — add a note to memory).
   - Skip items with `confidence < 0.7`.
   - Skip items with `severity < 3` if there are higher-severity items available.
3. Pick the top candidate by `(severity × confidence) / complexity_factor` where complexity_factor is `{S: 1, M: 2, L: 4}`.
4. Read the affected file fully via `read` tool. Read up to 3 adjacent files for context.
5. Draft the diff in your head. The diff MUST:
   - Be functionally identical (same tests pass)
   - Touch only one concern (e.g., extract one function, not also rename + reformat)
   - Be reversible by a human reviewer in under 2 minutes
6. Use `edit` to apply the change to the working copy at `${{ env.TARGET_DIR }}`.
7. Output a JSON plan describing what you did and why.

## Output Format

```json
{
  "smell_fingerprint": "string",
  "title": "Imperative-mood title, < 70 chars",
  "rationale": "1-3 sentence explanation of why this change improves the code",
  "files_changed": ["path/to/file.ts"],
  "lines_changed": int,
  "risk": "low|medium",
  "rollback_difficulty": "trivial|easy|moderate"
}
```

## Examples

**Input**: smell `{path: "src/cart.ts", lines: [42, 134], smell: "long_function", severity: 4, complexity: "M", confidence: 0.85}`.

**Output**:
```json
{
  "smell_fingerprint": "abc123",
  "title": "Extract pricing calculation from calculateCart",
  "rationale": "calculateCart at 92 lines mixes pricing, tax, and discount logic. Extract pricing into calculatePricing() — improves testability and matches the team convention of single-concern functions documented in memory/repos/widget-store-api/conventions.md.",
  "files_changed": ["src/cart.ts", "src/pricing.ts"],
  "lines_changed": 87,
  "risk": "low",
  "rollback_difficulty": "trivial"
}
```

## Notes

- If `lines_changed > 400`, abort and request approval via the workflow's `__approval_gate__` step (RULE 10).
- Cite the convention or memory entry that motivated the change in `rationale`.
- Refactors NEVER change observable behavior. If behavior changes, this is a bug fix, not a refactor — reclassify.
