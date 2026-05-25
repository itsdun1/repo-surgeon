#!/usr/bin/env python3
"""on_session_end hook — dedupes session scratch, merges into canonical memory, commits, pushes.

This is THE compounding moment. Every successful (or failed) session ends with a git
commit on the agent repo that captures what was learned, namespaced by target repo.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=30)
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except Exception as e:
        return -1, str(e)


def dedupe_lines(existing: str, new_entries: list[str]) -> list[str]:
    """Simple dedupe: skip new entries whose first 40 chars already appear in existing."""
    existing_norm = existing.lower()
    keep = []
    for entry in new_entries:
        key = entry.strip()[:40].lower()
        if key and key not in existing_norm:
            keep.append(entry)
    return keep


def merge_into_canonical(agent_dir: Path, target_repo: str, scratch_content: str, session_id: str) -> dict:
    """Parse scratch markdown, append unique entries to canonical files. Returns counts."""
    repo_key = target_repo.split("/")[-1] if "/" in target_repo else target_repo
    repo_mem = agent_dir / "memory" / "repos" / repo_key
    repo_mem.mkdir(parents=True, exist_ok=True)

    kind_to_file = {
        "LESSON": repo_mem / "lessons.md",
        "CONVENTION": repo_mem / "conventions.md",
        "SMELL": repo_mem / "code-smells.md",
        "WONT-FIX": repo_mem / "lessons.md",
    }

    # Extract entries from scratch
    pattern = re.compile(r"-\s+\*\*(LESSON|CONVENTION|SMELL|WONT-?FIX)\*\*:\s+(.+?)(?=\n-\s+\*\*|\n##|\Z)", re.DOTALL)
    entries: dict[str, list[str]] = {}
    for kind, body in pattern.findall(scratch_content):
        key = kind.replace("-", "").upper().replace("WONTFIX", "WONT-FIX")
        entries.setdefault(key, []).append(body.strip().replace("\n", " "))

    counts = {"lessons": 0, "conventions": 0, "smells": 0, "wont_fix": 0}
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for kind, items in entries.items():
        target_file = kind_to_file.get(kind)
        if not target_file:
            continue
        existing = target_file.read_text() if target_file.exists() else f"# {kind.lower()}.md for {target_repo}\n\n"
        new_entries = dedupe_lines(existing, items)
        if not new_entries:
            continue
        header_label = "Won't-fix" if kind == "WONT-FIX" else kind.capitalize()
        block = f"\n### {header_label} entries from session `{session_id}` ({ts})\n\n"
        for e in new_entries:
            block += f"- {e}\n"
        with target_file.open("a") as f:
            f.write(block)
        if kind == "LESSON":
            counts["lessons"] += len(new_entries)
        elif kind == "CONVENTION":
            counts["conventions"] += len(new_entries)
        elif kind == "SMELL":
            counts["smells"] += len(new_entries)
        elif kind == "WONT-FIX":
            counts["wont_fix"] += len(new_entries)

    return counts


def main():
    raw = sys.stdin.read()
    payload = json.loads(raw) if raw.strip() else {}
    session = payload.get("session", {})
    session_id = session.get("id", "unknown")
    target_repo = os.environ.get("TARGET_REPO", "unknown")
    agent_dir = Path(os.environ.get("AGENT_REPO_PATH", ".")).resolve()

    scratch = agent_dir / "memory" / "sessions" / f"{session_id}.md"
    if not scratch.exists() or not scratch.read_text().strip():
        print(json.dumps({"action": "allow", "audit": {"reason": "no learnings to commit"}}))
        return

    scratch_content = scratch.read_text()
    counts = merge_into_canonical(agent_dir, target_repo, scratch_content, session_id)

    if sum(counts.values()) == 0:
        # everything was duplicate; clean up scratch
        scratch.unlink(missing_ok=True)
        print(json.dumps({"action": "allow", "audit": {"reason": "all entries were duplicates"}}))
        return

    # Stage and commit
    rc, _ = run(["git", "add", "memory/"], agent_dir)
    if rc != 0:
        print(json.dumps({"action": "allow", "audit": {"error": "git add failed"}}))
        return

    msg = (
        f"surgeon-memory: {target_repo} | session={session_id} | "
        f"+{counts['lessons']} lessons, +{counts['conventions']} conventions, "
        f"+{counts['smells']} smells, +{counts['wont_fix']} won't-fix"
    )
    rc, out = run(["git", "commit", "-m", msg], agent_dir)
    if rc != 0:
        print(json.dumps({"action": "allow", "audit": {"error": f"git commit: {out[:200]}"}}))
        return

    # Push if we have a remote
    push_rc, push_out = run(["git", "push", "origin", "HEAD"], agent_dir)
    push_ok = push_rc == 0

    # Remove scratch (already captured in canonical files + git history)
    scratch.unlink(missing_ok=True)

    print(
        json.dumps(
            {
                "action": "allow",
                "audit": {
                    "committed": True,
                    "pushed": push_ok,
                    "counts": counts,
                    "commit_message": msg,
                    "push_output": push_out[:200] if not push_ok else None,
                },
            }
        )
    )


if __name__ == "__main__":
    main()
