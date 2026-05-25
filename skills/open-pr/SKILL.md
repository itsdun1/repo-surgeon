---
name: open-pr
description: >
  Push the working branch and open a pull request with a structured body. Final
  step before the human reviews. Uses the github-api tool.
license: Apache-2.0
allowed-tools: [cli, github-api]
metadata:
  author: repo-surgeon
  version: 1.0.0
  category: delivery
  risk_tier: medium
---

## Instructions

### 1. Compose the title
Format: `[surgeon:<kind>] <imperative-mood summary>` where `<kind>` is `fix`, `refactor`, or `feat`. Under 70 chars.

Examples:
- `[surgeon:fix] Handle decimal prices in cart total calculation`
- `[surgeon:refactor] Extract pricing logic from calculateCart`
- `[surgeon:feat] Add percentage discount support to checkout`

### 2. Compose the body
Use the template from `assets/pr-template.md`. Fill ALL five sections:

```markdown
## What changed
<1-3 bullet points describing the diff at a high level>

## Why
<2-4 sentences explaining the motivation — cite the issue, prior PR, or memory entry>

## How I tested
<list of test commands run + outcome>

## Risk
<honest assessment: low / medium / high — and what could go wrong>

## Sources
- Issue: #<number>
- Related PRs: #<number>, #<number>
- Memory entries: `memory/repos/<repo>/<file>.md#<section>`
```

### 3. Push the branch
Via `cli`:
```bash
cd ${TARGET_DIR}
git checkout -b surgeon/<session-id>  # branch name from session
git add <only the files you intended to change>
git commit -m "<title>"
git push origin surgeon/<session-id>
```

NEVER use `git add .` or `git add -A` — be explicit about which files to stage (RULE 7 against unintended commits).

### 4. Open the PR
Via `github-api` tool, action `open_pr`:
- `repo`: from `TARGET_REPO` env
- `branch`: `surgeon/<session-id>`
- `base`: the repo's default branch (usually `main`; check `memory/repos/<repo>/conventions.md`)
- `title`: from step 1
- `body`: from step 2
- `labels`: `["surgeon:<kind>", "needs-review"]`

### 5. Comment back on the source issue
If this PR resolves an issue, use `github-api` action `comment` to post: "Opened <PR URL> for review."

## Output Format

```json
{
  "pr_url": "string",
  "pr_number": int,
  "branch": "string",
  "title": "string",
  "labels": ["string"],
  "files_committed": ["string"],
  "commit_sha": "string"
}
```

## Notes

- **RULE 5: NEVER MERGE THE PR.** The `merge` permission is reserved for humans. The `enforce_rules.py` hook will block any merge attempt.
- **RULE 6: NEVER force-push** to any branch except your own working branch.
- If `github-api` returns 422 (PR already exists), check for an existing open PR on the same branch — update its body instead of opening a duplicate.
- Failures to push (auth issues, ref already exists) should abort, not retry indefinitely.
