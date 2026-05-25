#!/usr/bin/env python3
"""detect-conventions tool — analyzes target repo, writes memory/repos/<repo>/conventions.md."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def detect_language(wd: Path) -> str:
    counts: dict[str, int] = {}
    for p in wd.rglob("*"):
        if "/.git/" in str(p) or "/node_modules/" in str(p):
            continue
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        counts[ext] = counts.get(ext, 0) + 1
    mapping = {
        ".py": "Python",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".go": "Go",
        ".rs": "Rust",
        ".java": "Java",
        ".rb": "Ruby",
    }
    best = max(((mapping[k], v) for k, v in counts.items() if k in mapping), default=(None, 0))
    return best[0] or "Unknown"


def detect_test_framework(wd: Path, lang: str) -> str:
    if lang in ("TypeScript", "JavaScript"):
        pkg = wd / "package.json"
        if pkg.exists():
            try:
                content = json.loads(pkg.read_text())
                deps = {**content.get("dependencies", {}), **content.get("devDependencies", {})}
                for f in ("jest", "vitest", "mocha", "ava", "tap"):
                    if f in deps:
                        return f
            except Exception:
                pass
    if lang == "Python":
        if any(wd.rglob("pytest.ini")) or "pytest" in (wd / "pyproject.toml").read_text() if (wd / "pyproject.toml").exists() else False:
            return "pytest"
        return "pytest"  # assume default
    if lang == "Go":
        return "go test"
    if lang == "Rust":
        return "cargo test"
    return "unknown"


def detect_linter(wd: Path, lang: str) -> str:
    if lang in ("TypeScript", "JavaScript"):
        if any(wd.rglob(".eslintrc*")) or (wd / "eslint.config.js").exists():
            return "eslint"
    if lang == "Python":
        if (wd / "pyproject.toml").exists():
            content = (wd / "pyproject.toml").read_text()
            if "ruff" in content:
                return "ruff"
            if "flake8" in content:
                return "flake8"
        return "ruff"  # modern default
    if lang == "Go":
        return "golangci-lint"
    return "unknown"


def detect_formatter(wd: Path, lang: str) -> str:
    if lang in ("TypeScript", "JavaScript"):
        if any(wd.rglob(".prettierrc*")) or (wd / "prettier.config.js").exists():
            return "prettier"
    if lang == "Python":
        if (wd / "pyproject.toml").exists():
            content = (wd / "pyproject.toml").read_text()
            if "black" in content:
                return "black"
            if "ruff" in content:
                return "ruff format"
    if lang == "Go":
        return "gofmt"
    return "unknown"


def detect_import_style(wd: Path, lang: str) -> str:
    if lang == "TypeScript":
        # Sample first 20 .ts files
        samples = list(wd.rglob("*.ts"))[:20]
        rel_count = abs_count = 0
        for s in samples:
            if "/node_modules/" in str(s):
                continue
            try:
                content = s.read_text(errors="ignore")
            except Exception:
                continue
            rel_count += len(re.findall(r'from\s+["\']\.\.?\/', content))
            abs_count += len(re.findall(r'from\s+["\'][@a-zA-Z]', content))
        return "absolute" if abs_count > rel_count else "relative"
    if lang == "Python":
        return "absolute"  # PEP 8 preferred
    return "unknown"


def detect_pr_pattern(wd: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "log", "--all", "--pretty=%H %s", "-n", "100"],
            cwd=wd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        msgs = proc.stdout.splitlines()
        conv = sum(1 for m in msgs if re.match(r"^\w+\s+(feat|fix|refactor|docs|test|chore)(\(.+\))?:", m))
        return "conventional-commits" if conv > len(msgs) * 0.3 else "free-form"
    except Exception:
        return "unknown"


def write_conventions_md(agent_dir: Path, repo_name: str, findings: dict) -> str:
    repo_mem = agent_dir / "memory" / "repos" / repo_name
    repo_mem.mkdir(parents=True, exist_ok=True)
    f = repo_mem / "conventions.md"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    body = f"""# Conventions: {repo_name}

_Auto-detected by `detect-conventions` on {ts}._

## Stack
- **Language**: {findings['language']}
- **Test framework**: {findings['test_framework']}
- **Linter**: {findings['linter']}
- **Formatter**: {findings['formatter']}

## Code style
- **Import style**: {findings['import_style']}
- **Error handling**: {findings['error_handling']}

## Git
- **Commit message style**: {findings['pr_branch_pattern']}

## Notes
- This file is updated idempotently by the `detect-conventions` tool.
- Human-curated entries should go BELOW this auto-section, under a `## Human-curated` heading.
"""
    prev = f.read_text() if f.exists() else ""
    if prev == body:
        return "no changes"
    f.write_text(body)
    return f"updated {f}"


def main():
    raw = sys.stdin.read()
    args = json.loads(raw)
    wd = Path(args["working_dir"]).resolve()
    if not wd.exists():
        print(json.dumps({"error": f"working_dir does not exist: {wd}"}))
        return

    lang = detect_language(wd)
    findings = {
        "language": lang,
        "test_framework": detect_test_framework(wd, lang),
        "linter": detect_linter(wd, lang),
        "formatter": detect_formatter(wd, lang),
        "import_style": detect_import_style(wd, lang),
        "error_handling": "try/except (Python), throw (TS/JS), Result (Rust)" if lang in ("Python", "TypeScript", "JavaScript", "Rust") else "unknown",
        "pr_branch_pattern": detect_pr_pattern(wd),
        "primary_runtime": lang,
    }

    if args.get("write_to_memory", True):
        agent_dir = Path(args.get("agent_dir") or os.environ.get("AGENT_REPO_PATH", "./repo-surgeon")).resolve()
        try:
            findings["memory_diff"] = write_conventions_md(agent_dir, args["repo_name"], findings)
        except Exception as e:
            findings["memory_diff"] = f"error: {e}"

    print(json.dumps(findings))


if __name__ == "__main__":
    main()
