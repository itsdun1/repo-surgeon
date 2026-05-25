# Repo Surgeon (GAP Agent)

> A GitAgent Protocol (GAP) agent that lives across an org's repos and opens scoped, tested, well-explained PRs from issues and scheduled scans.

This directory is the **agent itself** — a fully-functioning GAP repo. It can be used standalone via `gitagent --dir ./repo-surgeon --prompt "..."` or driven by the wrapping platform (`surgeon-service`, `dashboard`).

## What's inside

```
repo-surgeon/
├── agent.yaml              # manifest: model, skills, tools, sub-agents, compliance
├── SOUL.md                 # personality and working style
├── RULES.md                # 24 hard rules enforced at pre_tool_use hook
├── skills/                 # 10 composable capabilities
├── tools/                  # 5 custom tools (MCP-compatible YAML + Python scripts)
├── hooks/                  # 5 lifecycle scripts (load memory, enforce rules, audit, learn, commit)
├── workflows/              # 2 SkillsFlow workflows: issue-to-pr, refactor-workflow
├── agents/                 # 1 lightweight sub-agent: security-reviewer
├── memory/                 # git-committed memory, namespaced by org + per-repo
└── evals/                  # golden test fixtures + multi-runtime scorer
```

## How to use this agent standalone

```bash
# Install the gitagent CLI
bash <(curl -fsSL "https://raw.githubusercontent.com/open-gitagent/gitagent/main/install.sh")

# Set the GitHub token for the API calls
export GITHUB_TOKEN=ghp_...
export ANTHROPIC_API_KEY=sk-ant-...

# Tell the agent which repo to work on (used by load_memory_namespace hook)
export TARGET_REPO=your-username/widget-store-api
export TARGET_DIR=/tmp/surgeon-workspace/manual/target
git clone https://github.com/$TARGET_REPO $TARGET_DIR

# Run the agent
gitagent --dir . --prompt "Read issue #1 on $TARGET_REPO and fix the bug. Open a PR."
```

## How memory namespacing works

Every session, the `load_memory_namespace.py` hook reads two layers:

1. **Org-wide** (`memory/org/`) — always loaded. Tech stack, team conventions, deploy process, glossary.
2. **Per-repo** (`memory/repos/<TARGET_REPO>/`) — loaded only when `TARGET_REPO` env matches. Conventions detected automatically, lessons accumulated from past sessions, code-smell backlog, additive RULES override.

When the session ends, the `commit_memory.py` hook dedupes session learnings into the canonical files, commits with a structured message, and pushes to the agent repo's GitHub origin.

**This is the compounding loop.** Every reviewed PR teaches the agent — visibly, in git history.

## Forking this agent for your own org

```bash
gh repo fork your-username/repo-surgeon
git clone https://github.com/your-org/repo-surgeon
cd repo-surgeon

# Edit RULES.md (your stricter constraints)
# Edit memory/org/* (your tech stack and team norms)
# Commit and push

# Point the platform at your fork
export AGENT_REPO_PATH=./repo-surgeon
export AGENT_REPO_REMOTE=https://github.com/your-org/repo-surgeon
```

The platform (`surgeon-service`) clones the agent repo on startup, pulls before each run, pushes memory updates after. Your org's agent diverges intelligently from upstream.

## Multi-runtime

The agent's `agent.yaml` declares model preferences:

```yaml
model:
  preferred: anthropic:claude-opus-4-7
  fallback:
    - anthropic:claude-sonnet-4-6
    - openai:gpt-5.1
```

The eval suite runs every fixture against **both Claude and OpenAI** to surface behavioral differences. The dashboard renders side-by-side diffs of what each model produced.

## License

Apache-2.0
