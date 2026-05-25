#!/usr/bin/env python3
"""dedupe-learnings.py — invoked by the update-memory skill.

Reads memory/sessions/<session-id>.md, dedupes entries against canonical files,
prints a summary. The actual write happens via commit_memory.py hook.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


def tokenize(s: str) -> set[str]:
    return {w for w in re.findall(r"\w+", s.lower()) if len(w) > 3}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--session", required=True)
    p.add_argument("--target-repo", required=True)
    p.add_argument("--agent-dir", default=os.environ.get("AGENT_REPO_PATH", "."))
    p.add_argument("--threshold", type=float, default=0.6)
    args = p.parse_args()

    agent_dir = Path(args.agent_dir).resolve()
    scratch = agent_dir / "memory" / "sessions" / f"{args.session}.md"
    if not scratch.exists():
        print(json.dumps({"error": f"no scratch file: {scratch}"}))
        return

    repo_key = args.target_repo.split("/")[-1]
    repo_mem = agent_dir / "memory" / "repos" / repo_key

    canonical = {}
    for name in ("lessons.md", "conventions.md", "code-smells.md"):
        f = repo_mem / name
        canonical[name] = f.read_text() if f.exists() else ""

    scratch_text = scratch.read_text()
    entry_re = re.compile(r"-\s+\*\*(LESSON|CONVENTION|SMELL|WONT-?FIX)\*\*:\s+(.+?)(?=\n-\s+\*\*|\n##|\Z)", re.DOTALL)

    findings = {"new": [], "duplicate": []}
    for kind, body in entry_re.findall(scratch_text):
        body = body.strip().replace("\n", " ")
        target = "lessons.md" if kind in ("LESSON", "WONT-FIX", "WONTFIX") else ("conventions.md" if kind == "CONVENTION" else "code-smells.md")
        existing_tokens = tokenize(canonical[target])
        new_tokens = tokenize(body)
        if existing_tokens and jaccard(existing_tokens, new_tokens) > args.threshold:
            findings["duplicate"].append({"kind": kind, "body": body[:80], "target": target})
        else:
            findings["new"].append({"kind": kind, "body": body[:80], "target": target})

    print(
        json.dumps(
            {
                "session": args.session,
                "target_repo": args.target_repo,
                "new_count": len(findings["new"]),
                "duplicate_count": len(findings["duplicate"]),
                "findings": findings,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
