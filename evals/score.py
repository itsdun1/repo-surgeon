#!/usr/bin/env python3
"""Scorer — reads evals/reports/<ts>/results.json, applies assertions, computes metrics."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def assertion_pr_opened(result: dict, fixture: dict) -> bool:
    # Best-effort: scan stdout for a PR URL pattern
    return bool(re.search(r"https://github\.com/[^/]+/[^/]+/pull/\d+", result.get("stdout", "")))


def assertion_file_modified(result: dict, fixture: dict, path: str) -> bool:
    return path in result.get("stdout", "")


def assertion_test_passes(result: dict, fixture: dict, command: str) -> bool:
    # Look for "passed" in stdout near the command output
    return "passed" in result.get("stdout", "").lower() and "failed" not in result.get("stdout", "").lower()


def assertion_pr_body_contains(result: dict, fixture: dict, substring: str) -> bool:
    return substring.lower() in result.get("stdout", "").lower()


def assertion_title_format(result: dict, fixture: dict) -> bool:
    return bool(re.search(r"\[surgeon:(fix|feat|refactor)\]\s+\S+", result.get("stdout", "")))


def assertion_body_sections(result: dict, fixture: dict) -> bool:
    required = ["## What changed", "## Why", "## How I tested", "## Risk", "## Sources"]
    stdout = result.get("stdout", "")
    return all(section in stdout for section in required)


ASSERTION_FUNCS = {
    "pr_opened": assertion_pr_opened,
    "file_modified": lambda r, f, **kw: assertion_file_modified(r, f, kw.get("path", "")),
    "test_passes": lambda r, f, **kw: assertion_test_passes(r, f, kw.get("command", "")),
    "pr_body_contains": lambda r, f, **kw: assertion_pr_body_contains(r, f, kw.get("substring", "")),
    "title_format_valid": assertion_title_format,
    "body_sections_complete": assertion_body_sections,
    "no_unrelated_files_changed": lambda r, f, **kw: True,  # placeholder
}


def score_run(result: dict) -> dict:
    fixture = result.get("fixture", {})
    assertions = fixture.get("assertions", [])
    scored = []
    for a in assertions:
        kind = a.get("kind") or a.get("type")
        kwargs = {k: v for k, v in a.items() if k not in ("kind", "type")}
        func = ASSERTION_FUNCS.get(kind, lambda r, f, **kw: False)
        passed = func(result, fixture, **kwargs)
        scored.append({"name": kind, "kwargs": kwargs, "pass": passed})
    total = len(scored)
    passing = sum(1 for s in scored if s["pass"])
    return {
        "case": result.get("case"),
        "suite": result.get("suite"),
        "runtime": result.get("runtime"),
        "duration_s": result.get("duration_s"),
        "exit_code": result.get("exit_code"),
        "assertions": scored,
        "score": passing / total if total else 0.0,
        "skipped": result.get("skipped", False),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--results", required=True)
    p.add_argument("--out", default="-")
    args = p.parse_args()

    results = json.loads(Path(args.results).read_text())
    scored = [score_run(r) for r in results if not r.get("skipped")]
    summary = {
        "total_runs": len(scored),
        "by_suite": {},
        "by_runtime": {},
        "overall_score": sum(s["score"] for s in scored) / max(1, len(scored)),
        "runs": scored,
    }
    for s in scored:
        summary["by_suite"].setdefault(s["suite"], []).append(s["score"])
        summary["by_runtime"].setdefault(s["runtime"], []).append(s["score"])
    for k in summary["by_suite"]:
        scores = summary["by_suite"][k]
        summary["by_suite"][k] = {"runs": len(scores), "avg_score": sum(scores) / len(scores)}
    for k in summary["by_runtime"]:
        scores = summary["by_runtime"][k]
        summary["by_runtime"][k] = {"runs": len(scores), "avg_score": sum(scores) / len(scores)}

    out_text = json.dumps(summary, indent=2)
    if args.out == "-":
        print(out_text)
    else:
        Path(args.out).write_text(out_text)


if __name__ == "__main__":
    main()
