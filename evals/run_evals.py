#!/usr/bin/env python3
"""Evaluation harness — runs the agent against fixture cases, captures behavior, scores.

For each suite × runtime × case, spawns the agent (or the relevant skill stub),
captures structured output, calls the scorer, writes a JSON report.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def load_eval_config(eval_yaml: Path) -> dict:
    return yaml.safe_load(eval_yaml.read_text())


def discover_cases(fixtures_dir: Path, glob_pattern: str) -> list[Path]:
    # glob_pattern is relative to the eval_yaml's directory
    return sorted([p for p in fixtures_dir.parent.glob(glob_pattern) if p.is_dir()])


def run_one(case_dir: Path, suite: dict, runtime: str, agent_dir: Path) -> dict:
    """Run agent against a single fixture case. Returns raw trace + meta."""
    fixture_yaml = case_dir / "fixture.yaml"
    if not fixture_yaml.exists():
        return {"case": str(case_dir), "error": "missing fixture.yaml"}
    fixture = yaml.safe_load(fixture_yaml.read_text())

    # Prepare ephemeral workspace
    workspace = Path(f"/tmp/surgeon-eval-{case_dir.name}-{int(time.time())}")
    workspace.mkdir(parents=True, exist_ok=True)

    # If the fixture provides a target_repo_archive, extract it
    archive_field = fixture.get("target_repo_archive")
    if archive_field:
        archive = case_dir / archive_field
        if archive.exists():
            subprocess.run(["tar", "-xzf", str(archive), "-C", str(workspace)], check=False)

    # Build prompt from fixture issue
    issue = fixture.get("issue", {})
    prompt = (
        f"Process this issue and produce structured output for the `{suite['skill']}` skill.\n\n"
        f"Title: {issue.get('title', '')}\n"
        f"Body: {issue.get('body', '')}\n"
        f"Labels: {', '.join(issue.get('labels', []))}\n"
    )

    cmd = [
        "gitagent",
        "--dir",
        str(agent_dir),
        "--prompt",
        prompt,
        "--model",
        runtime,
    ]
    env = {
        **os.environ,
        "TARGET_DIR": str(workspace),
        "TARGET_REPO": fixture.get("target_repo", "eval-target"),
        "EVAL_MODE": "1",
    }
    start = time.time()
    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=fixture.get("budget", {}).get("max_duration_s", 180))
        stdout = proc.stdout
        stderr = proc.stderr
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        stdout, stderr, exit_code = "", "TIMEOUT", -1
    except FileNotFoundError:
        # gitagent CLI not installed — skip with stub
        return {
            "case": case_dir.name,
            "suite": suite["name"],
            "runtime": runtime,
            "skipped": True,
            "reason": "gitagent CLI not installed",
        }
    duration = time.time() - start

    return {
        "case": case_dir.name,
        "suite": suite["name"],
        "runtime": runtime,
        "duration_s": duration,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "fixture": fixture,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="evals/eval.yaml")
    p.add_argument("--suite", help="Run only this suite")
    p.add_argument("--runtime", help="Override runtime list")
    p.add_argument("--agent-dir", default=os.environ.get("AGENT_REPO_PATH", "."))
    args = p.parse_args()

    cfg_path = Path(args.config).resolve()
    if not cfg_path.exists():
        print(json.dumps({"error": f"config not found: {cfg_path}"}))
        return
    cfg = load_eval_config(cfg_path)
    agent_dir = Path(args.agent_dir).resolve()

    suites = cfg["suites"]
    if args.suite:
        suites = [s for s in suites if s["name"] == args.suite]
    runtimes = [args.runtime] if args.runtime else cfg.get("runtimes", ["anthropic:claude-opus-4-7"])

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    reports_dir = agent_dir / "evals" / "reports" / ts
    reports_dir.mkdir(parents=True, exist_ok=True)

    all_results = []
    for suite in suites:
        cases = discover_cases(cfg_path.parent, suite["cases_glob"])
        for case in cases:
            for runtime in runtimes:
                result = run_one(case, suite, runtime, agent_dir)
                all_results.append(result)
                print(json.dumps({"progress": result.get("case"), "runtime": runtime, "exit_code": result.get("exit_code")}))

    (reports_dir / "results.json").write_text(json.dumps(all_results, indent=2))
    print(json.dumps({"reports_dir": str(reports_dir), "total_runs": len(all_results)}))


if __name__ == "__main__":
    main()
