---
name: classify-issue
description: >
  Read a GitHub issue (title, body, labels, comments) and classify it as bug,
  feature, refactor, won't-fix, or needs-clarification. Decides which workflow
  branch to execute.
license: Apache-2.0
allowed-tools: [read-issue]
metadata:
  author: repo-surgeon
  version: 1.0.0
  category: triage
  risk_tier: low
---

## Instructions

1. Use the `read-issue` tool to fetch the issue (title, body, labels, comments, linked PRs).
2. Read `memory/repos/<TARGET_REPO>/lessons.md` for prior won't-fix decisions.
3. Classify the issue into ONE of these categories:
   - **bug** — describes incorrect behavior; reproducible; should result in failing-test-then-fix
   - **feature** — requests new behavior or API
   - **refactor** — requests code cleanup with no behavior change
   - **wont-fix** — duplicate, out-of-scope, or matches a memory entry; comment and close
   - **needs-clarification** — too vague to act on; comment asking for repro steps, expected behavior, etc.
4. If the issue body lacks reproduction steps for a `bug` classification, flag as `needs-clarification` instead.
5. If classification is `feature`, estimate scope: `S` (1 file, <50 LOC), `M` (3-5 files, <200 LOC), `L` (>5 files or >200 LOC). For `L`, recommend the issue be split — comment with a proposed decomposition.

## Output Format

```json
{
  "kind": "bug | feature | refactor | wont-fix | needs-clarification",
  "scope": "S | M | L",
  "confidence": 0.0-1.0,
  "reasoning": "string",
  "comment_to_post": "string (optional, if wont-fix or needs-clarification)",
  "linked_memory_entries": ["path:section", ...]
}
```

## Examples

**Input**: Issue titled "Cart total wrong with decimals", body: "When prices have decimal cents (3.99 + 1.50), the total shows 5.4 instead of 5.49", labels: `["bug", "surgeon:fix"]`.

**Output**:
```json
{
  "kind": "bug",
  "scope": "S",
  "confidence": 0.95,
  "reasoning": "Concrete repro steps. Decimal arithmetic bug, likely in cart calculation. One module affected.",
  "linked_memory_entries": ["memory/repos/widget-store-api/conventions.md#money-handling"]
}
```

## Notes

- Never proceed past classification on a `wont-fix` or `needs-clarification` — emit the comment and stop.
- For `bug`: the workflow will then invoke `fix-from-issue`.
- For `feature`: the workflow will invoke `implement-feature`, possibly with an approval gate.
