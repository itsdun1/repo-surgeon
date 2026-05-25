---
name: load-repo-context
description: >
  Load the target repo's memory namespace into context at session start.
  Reads org-wide memory plus the per-repo subdirectory matching env TARGET_REPO.
  Always invoked first.
license: Apache-2.0
allowed-tools: [read, memory]
metadata:
  author: repo-surgeon
  version: 1.0.0
  category: bootstrap
  risk_tier: low
---

## Instructions

This skill runs at session start. It loads the agent's accumulated memory for the current target repo so subsequent skills have context.

1. Read `memory/MEMORY.md` — the top-level index of all memory namespaces.
2. Read every file under `memory/org/` — these are org-wide truths (tech stack, team conventions, deploy process, glossary).
3. From the `TARGET_REPO` env var, derive the per-repo namespace: `memory/repos/<TARGET_REPO>/`. Read every file in that directory:
   - `conventions.md` — repo-specific code conventions, naming, structure
   - `code-smells.md` — open backlog of known issues
   - `lessons.md` — past mistakes and non-obvious truths
   - `RULES-override.md` — additive constraints for this repo (if present)
4. If `memory/repos/<TARGET_REPO>/` does not exist, this is the first time the agent is working on this repo. Create the directory structure with empty files and a stub message: "First session — conventions, smells, and lessons will accumulate here."
5. Summarize the loaded context in your internal reasoning. You don't need to repeat it back to the user, but you must reference it when making decisions.

## Output Format

No structured output. Memory contents are now part of your working context. The `load_memory_namespace.py` hook handles the actual file reads at `on_session_start`; this skill exists so you (the model) know what to do when invoked explicitly.

## Notes

- Memory is git-tracked. Reviewers can curate it via PR review of the agent repo.
- The `RULES-override.md` file is additive — it cannot relax constraints in the top-level `RULES.md`.
- If a memory file is over 500 lines, focus on the most recent entries first.
