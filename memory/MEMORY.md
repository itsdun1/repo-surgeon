# Repo Surgeon — Memory Index

This file is the top-level index of the agent's accumulated knowledge. It's read at every session start (via `load_memory_namespace.py` hook).

**Last full audit**: 2026-05-25 (initial scaffold — empty)

## Org-level memory (`memory/org/`)

Always loaded for every session, regardless of target repo.

- `tech-stack.md` — current tech choices across all repos
- `team-conventions.md` — code review norms, PR culture, naming rules
- `deploy-process.md` — how code reaches production
- `glossary.md` — domain terms, project names, internal acronyms

## Per-repo memory (`memory/repos/<repo-name>/`)

Loaded only when `TARGET_REPO` env matches. Each repo namespace contains:

- `conventions.md` — repo-specific code conventions (auto-populated by `detect-conventions`, then human-curated)
- `code-smells.md` — ranked open backlog of smells discovered during scans
- `lessons.md` — non-obvious truths learned from past PRs; won't-fix entries
- `RULES-override.md` — additive constraints for this repo (cannot relax top-level RULES.md)

## Active repos

| Repo | Last activity | Open PRs | Memory size |
|------|---------------|----------|-------------|
| (none yet) | — | — | — |

This table is updated by the `commit_memory.py` hook after each session.

## Session scratch (`memory/sessions/`)

Ephemeral per-session learnings, captured by `extract_learnings.py` from `LESSON:`, `CONVENTION:`, `SMELL:`, `WONT-FIX:` sentinel lines in the agent's responses. Deduped and merged into canonical files by `commit_memory.py` at session end. Discarded after 30 days.

## Archive (`memory/archive/`)

Rotated content from above when files exceed their `max_lines` cap (per `memory.yaml`).

---

## How to curate memory (for humans)

This memory tree is yours to edit. The agent reads what you write. When you review a PR and have a teaching moment, the best move is:

1. Add the lesson/convention to the relevant file in `memory/repos/<repo>/`
2. Commit and push to this agent repo
3. Next time the agent works on that repo, it loads your edit

The agent will cite your memory entries in PR bodies when they inform a decision. If it gets something wrong, the fix is to update memory and re-trigger.
