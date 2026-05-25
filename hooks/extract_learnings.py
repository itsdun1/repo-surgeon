#!/usr/bin/env python3
"""post_response hook — scans assistant responses for LESSON/CONVENTION/SMELL/WONT-FIX sentinels.

Captures matches into memory/sessions/<session-id>.md (ephemeral scratch).
The commit_memory hook later dedupes and merges these into canonical memory files.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


SENTINELS = {
    "LESSON": re.compile(r"^\s*LESSON:\s*(.+?)$", re.MULTILINE),
    "CONVENTION": re.compile(r"^\s*CONVENTION:\s*(.+?)$", re.MULTILINE),
    "SMELL": re.compile(r"^\s*SMELL:\s*(.+?)$", re.MULTILINE),
    "WONT-FIX": re.compile(r"^\s*WONT-?FIX:\s*(.+?)$", re.MULTILINE | re.IGNORECASE),
}


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        print(json.dumps({"action": "allow"}))
        return

    payload = json.loads(raw)
    data = payload.get("data", {})
    response = data.get("response") or ""
    session = payload.get("session", {})
    session_id = session.get("id", "unknown")

    findings: dict[str, list[str]] = {}
    for kind, pat in SENTINELS.items():
        matches = [m.strip() for m in pat.findall(response)]
        if matches:
            findings[kind] = matches

    if not findings:
        print(json.dumps({"action": "allow", "audit": {"learnings_extracted": 0}}))
        return

    agent_dir = Path(os.environ.get("AGENT_REPO_PATH", ".")).resolve()
    session_dir = agent_dir / "memory" / "sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    scratch = session_dir / f"{session_id}.md"

    ts = datetime.now(timezone.utc).isoformat()
    target = os.environ.get("TARGET_REPO", "unknown")

    with scratch.open("a") as f:
        f.write(f"\n## Turn @ {ts} ({target})\n\n")
        for kind, items in findings.items():
            for item in items:
                f.write(f"- **{kind}**: {item}\n")

    total = sum(len(v) for v in findings.values())
    print(
        json.dumps(
            {
                "action": "allow",
                "audit": {
                    "learnings_extracted": total,
                    "kinds": list(findings.keys()),
                    "scratch_file": str(scratch.relative_to(agent_dir)),
                },
            }
        )
    )


if __name__ == "__main__":
    main()
