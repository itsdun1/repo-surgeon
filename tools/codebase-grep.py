#!/usr/bin/env python3
"""codebase-grep tool — text search over the target repo.

Prefers ripgrep (rg) if installed, falls back to git grep. JSON in/out.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def have_rg() -> bool:
    return shutil.which("rg") is not None


def run_ripgrep(args: dict) -> dict:
    cmd = ["rg", "--json", "--no-heading", "--with-filename"]
    if not args.get("case_sensitive", False):
        cmd.append("-i")
    if args.get("mode") == "literal":
        cmd.append("-F")
    elif args.get("mode") == "word":
        cmd.append("-w")
    for g in args.get("include_globs", []):
        cmd.extend(["-g", g])
    for g in args.get("exclude_globs", []):
        cmd.extend(["-g", f"!{g}"])
    max_results = args.get("max_results", 30)
    cmd.extend(["-m", str(max_results)])
    cmd.append(args["query"])
    cmd.append(args["working_dir"])
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=55)
    except subprocess.TimeoutExpired:
        return {"matches": [], "error": "timeout"}
    matches = []
    truncated = False
    for line in proc.stdout.splitlines():
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("type") != "match":
            continue
        data = obj["data"]
        matches.append(
            {
                "path": data["path"]["text"],
                "line": data["line_number"],
                "snippet": data["lines"]["text"].rstrip("\n"),
            }
        )
        if len(matches) >= max_results:
            truncated = True
            break
    return {
        "matches": matches,
        "total_matches": len(matches),
        "truncated": truncated,
    }


def run_git_grep(args: dict) -> dict:
    cmd = ["git", "grep", "-n"]
    if not args.get("case_sensitive", False):
        cmd.append("-i")
    if args.get("mode") == "literal":
        cmd.append("-F")
    elif args.get("mode") == "word":
        cmd.append("-w")
    cmd.append("-E" if args.get("mode") == "regex" else "")
    cmd = [c for c in cmd if c]
    cmd.extend(["--max-depth", "30"])
    cmd.append(args["query"])
    try:
        proc = subprocess.run(
            cmd,
            cwd=args["working_dir"],
            capture_output=True,
            text=True,
            timeout=55,
        )
    except subprocess.TimeoutExpired:
        return {"matches": [], "error": "timeout"}
    matches = []
    max_results = args.get("max_results", 30)
    for raw in proc.stdout.splitlines():
        parts = raw.split(":", 2)
        if len(parts) < 3:
            continue
        path, line_str, snippet = parts
        try:
            line = int(line_str)
        except ValueError:
            continue
        matches.append({"path": path, "line": line, "snippet": snippet.strip()})
        if len(matches) >= max_results:
            break
    return {
        "matches": matches,
        "total_matches": len(matches),
        "truncated": len(matches) >= max_results,
    }


def main():
    raw = sys.stdin.read()
    args = json.loads(raw)
    working_dir = Path(args["working_dir"]).expanduser().resolve()
    if not working_dir.exists():
        print(json.dumps({"matches": [], "error": "working_dir does not exist"}))
        return
    args["working_dir"] = str(working_dir)
    if have_rg():
        result = run_ripgrep(args)
    else:
        result = run_git_grep(args)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
