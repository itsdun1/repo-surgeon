#!/usr/bin/env python3
"""on_session_start hook — loads org + per-repo memory into agent context.

Reads JSON from stdin: {event, timestamp, data, session}
Writes JSON to stdout: {action: "modify"|"allow", modifications, audit}
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main():
    raw = sys.stdin.read()
    payload = json.loads(raw) if raw.strip() else {}

    agent_dir = Path(os.environ.get("AGENT_REPO_PATH", ".")).resolve()
    target_repo = os.environ.get("TARGET_REPO", "")

    context_blocks = []

    # 1. Always load top-level index
    memory_md = agent_dir / "memory" / "MEMORY.md"
    if memory_md.exists():
        context_blocks.append(f"<memory:index>\n{memory_md.read_text()}\n</memory:index>")

    # 2. Always load org-wide memory
    org_dir = agent_dir / "memory" / "org"
    if org_dir.exists():
        for f in sorted(org_dir.glob("*.md")):
            try:
                context_blocks.append(
                    f"<memory:org file=\"{f.name}\">\n{f.read_text()}\n</memory:org>"
                )
            except Exception:
                continue

    # 3. Load per-repo memory if TARGET_REPO is set
    if target_repo:
        # repo name might be "owner/repo" — use just the repo part for the dir name
        repo_key = target_repo.split("/")[-1] if "/" in target_repo else target_repo
        repo_dir = agent_dir / "memory" / "repos" / repo_key
        if not repo_dir.exists():
            repo_dir.mkdir(parents=True, exist_ok=True)
            for stub in ("conventions.md", "code-smells.md", "lessons.md"):
                p = repo_dir / stub
                if not p.exists():
                    p.write_text(
                        f"# {stub.replace('.md', '')} for {target_repo}\n\n"
                        f"_First session — this file will accumulate as the agent works on this repo._\n"
                    )
        for f in sorted(repo_dir.glob("*.md")):
            try:
                context_blocks.append(
                    f"<memory:repo:{repo_key} file=\"{f.name}\">\n{f.read_text()}\n</memory:repo>"
                )
            except Exception:
                continue

    result = {
        "action": "modify" if context_blocks else "allow",
        "modifications": {
            "context_prepend": "\n\n".join(context_blocks),
        },
        "audit": {
            "namespace_loaded": target_repo,
            "blocks_count": len(context_blocks),
            "agent_dir": str(agent_dir),
        },
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
