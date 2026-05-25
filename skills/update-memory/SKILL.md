---
name: update-memory
description: >
  Dedupe session learnings against existing memory files, append new entries,
  stage and commit. Runs at session end.
license: Apache-2.0
allowed-tools: [read, edit, write, memory]
metadata:
  author: repo-surgeon
  version: 1.0.0
  category: learning
  risk_tier: low
---

## Instructions

This skill is typically invoked by the `commit_memory.py` hook at `on_session_end`, but can be called explicitly.

### 1. Read the session scratch
Read `memory/sessions/<session-id>.md`. This was populated by `extract_learnings.py` during the session with `LESSON:`, `CONVENTION:`, `SMELL:`, and `WONT-FIX:` sentinel lines.

### 2. Categorize each entry
- `CONVENTION:` → `memory/repos/<TARGET_REPO>/conventions.md`
- `LESSON:` → `memory/repos/<TARGET_REPO>/lessons.md`
- `SMELL:` → `memory/repos/<TARGET_REPO>/code-smells.md`
- `WONT-FIX:` → `memory/repos/<TARGET_REPO>/lessons.md` under the "Won't-fix" section

### 3. Dedupe
For each new entry, scan the destination file for semantic duplicates.
- Run the dedupe script: `python scripts/dedupe-learnings.py --session <id> --target-repo <name>`.
- The script uses fuzzy matching (Jaccard similarity > 0.6 on tokens) to flag duplicates.
- For duplicates, either:
  - Skip the new entry if the existing one is more complete
  - Update the existing entry if the new entry adds detail
- Always preserve a timestamp on every entry.

### 4. Append in canonical format
Use this format for new entries:

```markdown
### {{ short_title }} ({{ YYYY-MM-DD }})

{{ body }}

**Source**: session `{{ session_id }}` (PR {{ pr_url }})
```

### 5. Commit and push
This step is handled by `commit_memory.py` hook. Commit message template:
```
surgeon-memory: <target-repo> | session=<id> | +<N> lessons, +<M> conventions, +<K> smells

Sources:
- PR <pr_url>
- Issue <issue_url>
```

Then `git push origin main` (to the agent repo's GitHub remote).

## Output Format

```json
{
  "session_id": "string",
  "target_repo": "string",
  "entries_added": {
    "conventions": int,
    "lessons": int,
    "smells": int,
    "wont_fix": int
  },
  "duplicates_skipped": int,
  "files_modified": ["memory/..."],
  "commit_sha": "string"
}
```

## Notes

- **RULE 19**: scrub any tokens, API keys, or PII from entries before saving. The hook also does this, but you are responsible too.
- If the session ended in failure (no PR opened), still save lessons — the failure itself is valuable knowledge.
- Memory files have soft size caps in `memory.yaml`. If a file exceeds its cap after this update, the rotation logic in `commit_memory.py` will archive the oldest entries to `memory/archive/`.
