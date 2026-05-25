---
name: scan-for-smells
description: >
  Scan the target repo for code smells (long functions, duplication, dead code,
  stale TODOs, complexity hotspots). Score and output a ranked backlog. Read-only.
license: Apache-2.0
allowed-tools: [cli, read, codebase-grep, detect-conventions]
metadata:
  author: repo-surgeon
  version: 1.0.0
  category: analysis
  risk_tier: low
---

## Instructions

1. Load `memory/repos/<TARGET_REPO>/code-smells.md` for the existing backlog and prior "won't fix" entries.
2. Run heuristics via `cli` tool:
   - **Long functions**: find functions > 60 lines (use `awk` / language-specific tools per `detect-conventions`)
   - **Cyclomatic complexity**: > 12 (use language-specific linter if available)
   - **Large files**: > 600 lines of code
   - **Duplicate blocks**: 8+ token, 3+ occurrences, via `codebase-grep`
   - **Stale TODOs**: TODO/FIXME comments older than 90 days (cross-reference with `git blame`)
   - **Dead code**: exported functions/classes with zero callers in the codebase
3. For each candidate smell, attach:
   - `path` — file path relative to repo root
   - `lines` — `[start, end]` line range
   - `smell` — one of: `long_function`, `high_complexity`, `large_file`, `duplicate_block`, `stale_todo`, `dead_code`
   - `severity` — 1 (low) to 5 (high)
   - `complexity` — `S`, `M`, or `L` (estimated fix effort)
   - `confidence` — 0.0 to 1.0
   - `fingerprint` — stable hash of `(path, smell, content)` for deduplication
4. Cross-reference with `memory/repos/<TARGET_REPO>/conventions.md` to skip entries marked "intentional".
5. Dedupe against existing backlog by fingerprint. Mark new items as `new`, items present in last scan but still open as `persistent`, items resolved as `fixed`.

## Output Format

```json
{
  "scan_id": "string",
  "repo": "string",
  "scanned_at": "ISO-8601",
  "candidates": [
    {
      "path": "string",
      "lines": [int, int],
      "smell": "string",
      "severity": 1-5,
      "complexity": "S|M|L",
      "confidence": 0.0-1.0,
      "fingerprint": "string",
      "status": "new|persistent|fixed"
    }
  ],
  "skipped": [{"path": "string", "reason": "string"}]
}
```

## Notes

- **READ ONLY**. Never invoke `write` or `edit` from this skill.
- Never propose a refactor for code under active development (last commit < 7 days). Check via `git log --since="7 days ago"`.
- Output is consumed by `propose-refactor`.
- This skill respects RULES.md — forbidden paths are silently skipped.
