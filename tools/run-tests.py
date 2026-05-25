#!/usr/bin/env python3
"""run-tests tool — auto-detects test runner and executes the suite.

Returns parsed pass/fail with failure context. Used by run-tests-validate skill.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


def detect_runner(working_dir: Path) -> tuple[str, str] | None:
    """Return (runner_name, command_template). command uses {scope}/{files} placeholders."""
    pkg_json = working_dir / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text())
            scripts = pkg.get("scripts", {})
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "test" in scripts:
                # Prefer the package's own test script
                if "jest" in deps:
                    return ("jest", "npx jest --no-coverage {files}")
                if "vitest" in deps:
                    return ("vitest", "npx vitest run {files}")
                if "mocha" in deps:
                    return ("mocha", "npx mocha {files}")
                return ("npm-test", "npm test --silent")
        except Exception:
            pass

    if (working_dir / "pyproject.toml").exists() or (working_dir / "setup.py").exists():
        # Try pytest first
        if any((working_dir / d).exists() for d in ["tests", "test"]):
            return ("pytest", "python -m pytest {files} -x --tb=short")
        return ("pytest", "python -m pytest {files} -x --tb=short")

    if (working_dir / "go.mod").exists():
        return ("go-test", "go test {files}")

    if (working_dir / "Cargo.toml").exists():
        return ("cargo-test", "cargo test {files}")

    if (working_dir / "pom.xml").exists():
        return ("maven", "mvn test {files}")

    if (working_dir / "build.gradle").exists() or (working_dir / "build.gradle.kts").exists():
        return ("gradle", "./gradlew test {files}")

    if (working_dir / "Gemfile").exists():
        return ("rspec", "bundle exec rspec {files}")

    return None


def changed_files(working_dir: Path) -> list[str]:
    """Files changed in the current working tree vs HEAD."""
    try:
        res = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return [f.strip() for f in res.stdout.splitlines() if f.strip()]
    except Exception:
        return []


def build_files_arg(runner: str, scope: str, target_files: list[str], working_dir: Path) -> str:
    if scope == "all":
        return ""
    if scope == "file":
        return " ".join(target_files) if target_files else ""
    # changed
    files = changed_files(working_dir)
    # Filter to likely test files or files that should map to tests
    if runner.startswith("pytest"):
        test_files = [f for f in files if "test_" in f or f.endswith("_test.py") or "/tests/" in f]
        return " ".join(test_files) if test_files else ""
    elif runner in ("jest", "vitest", "mocha"):
        test_files = [f for f in files if ".test." in f or ".spec." in f or "/__tests__/" in f]
        return " ".join(test_files) if test_files else ""
    return ""


PYTEST_FAIL_RE = re.compile(r"FAILED (\S+)::(\S+)\s*-\s*(.+)")
JEST_FAIL_RE = re.compile(r"●\s+(.+)\n\s+(.+)")


def parse_failures(runner: str, stdout: str) -> list[dict]:
    failures = []
    if runner.startswith("pytest"):
        for m in PYTEST_FAIL_RE.finditer(stdout):
            failures.append(
                {"test": f"{m.group(1)}::{m.group(2)}", "error": m.group(3).strip(), "stack": ""}
            )
    elif runner in ("jest", "vitest"):
        for m in JEST_FAIL_RE.finditer(stdout):
            failures.append({"test": m.group(1).strip(), "error": m.group(2).strip(), "stack": ""})
    return failures


def parse_summary(runner: str, stdout: str) -> dict:
    summary = {"passed": 0, "failed": 0, "skipped": 0}
    if runner.startswith("pytest"):
        # "5 passed, 2 failed, 1 skipped in 1.23s"
        m = re.search(r"(\d+) passed", stdout)
        if m:
            summary["passed"] = int(m.group(1))
        m = re.search(r"(\d+) failed", stdout)
        if m:
            summary["failed"] = int(m.group(1))
        m = re.search(r"(\d+) skipped", stdout)
        if m:
            summary["skipped"] = int(m.group(1))
    elif runner in ("jest", "vitest"):
        m = re.search(r"Tests:\s+(?:(\d+) failed,\s+)?(?:(\d+) skipped,\s+)?(\d+) passed", stdout)
        if m:
            summary["failed"] = int(m.group(1) or 0)
            summary["skipped"] = int(m.group(2) or 0)
            summary["passed"] = int(m.group(3) or 0)
    elif runner == "go-test":
        summary["passed"] = stdout.count("--- PASS:")
        summary["failed"] = stdout.count("--- FAIL:")
        summary["skipped"] = stdout.count("--- SKIP:")
    return summary


def main():
    raw = sys.stdin.read()
    args = json.loads(raw)
    working_dir = Path(args["working_dir"]).expanduser().resolve()
    if not working_dir.exists():
        print(
            json.dumps(
                {"tests_can_run": False, "error": f"working_dir does not exist: {working_dir}"}
            )
        )
        return

    scope = args.get("scope", "changed")
    target_files = args.get("target_files", [])
    timeout_s = args.get("timeout_s", 600)
    runner_override = args.get("runner_override")

    detected = (runner_override, "{runner} {files}") if runner_override else detect_runner(working_dir)
    if not detected:
        print(
            json.dumps(
                {
                    "tests_can_run": False,
                    "error": "Could not detect test runner. No package.json, pyproject.toml, go.mod, Cargo.toml, pom.xml, build.gradle, or Gemfile found.",
                }
            )
        )
        return

    runner, cmd_template = detected
    files_arg = build_files_arg(runner, scope, target_files, working_dir)
    command = cmd_template.format(files=files_arg, runner=runner).strip()
    if scope == "changed" and not files_arg:
        # No changed test files found; run all to be safe
        command = cmd_template.format(files="", runner=runner).strip()

    start = time.time()
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        print(
            json.dumps(
                {
                    "runner": runner,
                    "command_used": command,
                    "tests_can_run": False,
                    "error": f"timeout after {timeout_s}s",
                    "exit_code": -1,
                }
            )
        )
        return
    duration = time.time() - start
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    summary = parse_summary(runner, combined)
    failures = parse_failures(runner, combined)

    result = {
        "runner": runner,
        "command_used": command,
        "passed": summary["passed"],
        "failed": summary["failed"],
        "skipped": summary["skipped"],
        "duration_s": round(duration, 2),
        "failures": failures,
        "exit_code": proc.returncode,
        "tests_can_run": True,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
