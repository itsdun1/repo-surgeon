#!/usr/bin/env python3
"""post_tool_use + on_error hook — appends a redacted JSON line to audit-trail.jsonl."""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


REDACT_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9_]{30,}"),
    re.compile(r"gho_[A-Za-z0-9_]{30,}"),
    re.compile(r"ghs_[A-Za-z0-9_]{30,}"),
    re.compile(r"sk-[A-Za-z0-9_\-]{30,}"),
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{30,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access keys
    re.compile(r"-----BEGIN [A-Z ]+ KEY-----[\s\S]+?-----END [A-Z ]+ KEY-----"),
]


def redact(text: str) -> str:
    for pat in REDACT_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        print(json.dumps({"action": "allow"}))
        return

    payload = json.loads(raw)
    event = payload.get("event", "unknown")
    session = payload.get("session", {})
    data = payload.get("data", {})

    # Build a single redacted summary entry
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "session_id": session.get("id"),
        "agent": session.get("agent"),
        "turn": session.get("turn"),
        "tool": data.get("tool_name"),
        "arguments_summary": redact(json.dumps(data.get("arguments", {}))[:500]),
        "result_summary": redact(json.dumps(data.get("result", {}))[:500]),
        "error": redact(str(data.get("error", "")))[:500] if data.get("error") else None,
    }

    agent_dir = Path(os.environ.get("AGENT_REPO_PATH", ".")).resolve()
    log_path = agent_dir / "hooks" / "audit-trail.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as f:
        f.write(json.dumps(entry) + "\n")

    print(json.dumps({"action": "allow", "audit": {"logged": True}}))


if __name__ == "__main__":
    main()
