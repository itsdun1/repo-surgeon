#!/usr/bin/env python3
"""pre_tool_use hook — enforces RULES.md against every tool call.

Returns {action: "block", reason: "..."} for violations.
Returns {action: "allow"} for permitted calls.
"""
from __future__ import annotations

import fnmatch
import json
import os
import sys
from pathlib import Path


FORBIDDEN_GLOBS = [
    "**/migrations/**",
    "**/*.env",
    "**/*.env.*",
    "**/.env",
    "**/secrets/**",
    "**/.github/workflows/**",
    "Dockerfile",
    "Dockerfile.*",
    "**/Dockerfile",
    "**/terraform/**",
    "**/k8s/**",
    "**/helm/**",
    "**/charts/**",
    "**/*.pem",
    "**/*.key",
    "**/*.crt",
]

BINARY_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".zip", ".tar", ".gz", ".so", ".dll", ".exe", ".pdf", ".woff", ".woff2"}

# Git commands that violate rules 5, 6, 7
UNSAFE_GIT_PATTERNS = [
    "push --force",
    "push -f",
    "push --force-with-lease",  # still risky on shared branches
    "reset --hard origin",
    "filter-branch",
    " merge ",  # blocked unless --no-commit (we'd parse more carefully)
]


def matches_forbidden(path: str) -> str | None:
    """Return matching glob, or None."""
    path = path.lstrip("./")
    for g in FORBIDDEN_GLOBS:
        if fnmatch.fnmatch(path, g):
            return g
    return None


def main():
    raw = sys.stdin.read()
    payload = json.loads(raw) if raw.strip() else {}
    data = payload.get("data", {})
    tool_name = data.get("tool_name", "")
    args = data.get("arguments", {}) or {}

    # --- write / edit checks ---
    if tool_name in ("write", "edit"):
        file_path = args.get("file_path") or args.get("path") or ""
        glob = matches_forbidden(file_path)
        if glob:
            print(
                json.dumps(
                    {
                        "action": "block",
                        "reason": f"RULE-1: cannot modify '{file_path}' — matches forbidden glob '{glob}'. Abort and comment on the issue.",
                        "audit": {"rule": "RULE-1", "path": file_path, "glob": glob},
                    }
                )
            )
            return
        ext = os.path.splitext(file_path)[1].lower()
        if ext in BINARY_EXTS:
            print(
                json.dumps(
                    {
                        "action": "block",
                        "reason": f"RULE-3: cannot commit binary file '{file_path}' (extension {ext}).",
                        "audit": {"rule": "RULE-3", "path": file_path},
                    }
                )
            )
            return

    # --- cli git checks ---
    if tool_name == "cli":
        cmd = (args.get("command") or "").strip()
        for pattern in UNSAFE_GIT_PATTERNS:
            if pattern in cmd and not cmd.endswith("# surgeon:approved"):
                # allow if explicitly tagged (escape hatch for human-approved workflows)
                print(
                    json.dumps(
                        {
                            "action": "block",
                            "reason": f"RULE-5/6: unsafe git operation detected — '{pattern}'. Blocked.",
                            "audit": {"rule": "RULE-5/6", "command": cmd[:200]},
                        }
                    )
                )
                return
        # Block git add . / -A (RULE 7 — be explicit)
        if cmd.startswith("git add") and (" ." in cmd or " -A" in cmd or " --all" in cmd):
            print(
                json.dumps(
                    {
                        "action": "block",
                        "reason": "RULE-7: do not use 'git add .' or '-A' — stage files explicitly to avoid committing unintended changes.",
                        "audit": {"rule": "RULE-7", "command": cmd[:200]},
                    }
                )
            )
            return

    # --- github-api checks ---
    if tool_name == "github-api":
        action = args.get("action", "")
        if action == "open_pr":
            # Default branch protection: ensure base != working branch
            base = args.get("base", "main")
            branch = args.get("branch", "")
            if branch == base:
                print(
                    json.dumps(
                        {
                            "action": "block",
                            "reason": "RULE-7: branch and base cannot be the same.",
                            "audit": {"rule": "RULE-7"},
                        }
                    )
                )
                return
        if action == "merge":
            print(
                json.dumps(
                    {
                        "action": "block",
                        "reason": "RULE-5: the agent NEVER self-merges. Merge is a human action.",
                        "audit": {"rule": "RULE-5", "action": "merge"},
                    }
                )
            )
            return

    # All clear
    print(json.dumps({"action": "allow"}))


if __name__ == "__main__":
    main()
