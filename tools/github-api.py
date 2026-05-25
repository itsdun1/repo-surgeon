#!/usr/bin/env python3
"""github-api tool — interacts with the GitHub REST API on behalf of repo-surgeon.

Reads action + params from stdin (JSON), writes result to stdout (JSON).
Auth via GITHUB_TOKEN env (set by the dispatcher per run).
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any

import urllib.request
import urllib.error


GITHUB_API = "https://api.github.com"


def _request(method: str, path: str, body: dict | None = None) -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN env not set")
    url = f"{GITHUB_API}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "repo-surgeon")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode())
        except Exception:
            err_body = {"message": str(e)}
        raise RuntimeError(f"GitHub API {e.code}: {err_body}") from e


def open_pr(args: dict) -> dict:
    repo = args["repo"]
    body = {
        "title": args["title"],
        "head": args["branch"],
        "base": args.get("base", "main"),
        "body": args.get("body", ""),
        "draft": args.get("draft", False),
    }
    pr = _request("POST", f"/repos/{repo}/pulls", body)
    pr_number = pr["number"]
    if args.get("labels"):
        _request(
            "POST",
            f"/repos/{repo}/issues/{pr_number}/labels",
            {"labels": args["labels"]},
        )
    return {"success": True, "pr_number": pr_number, "pr_url": pr["html_url"]}


def comment(args: dict) -> dict:
    repo = args["repo"]
    issue_number = args["issue_number"]
    body = {"body": args.get("comment_body", args.get("body", ""))}
    res = _request("POST", f"/repos/{repo}/issues/{issue_number}/comments", body)
    return {"success": True, "comment_id": res["id"], "comment_url": res["html_url"]}


def label(args: dict) -> dict:
    repo = args["repo"]
    issue_number = args["issue_number"]
    body = {"labels": args["labels"]}
    res = _request("POST", f"/repos/{repo}/issues/{issue_number}/labels", body)
    return {"success": True, "labels_now": [l["name"] for l in res]}


def get_issue(args: dict) -> dict:
    repo = args["repo"]
    issue_number = args["issue_number"]
    issue = _request("GET", f"/repos/{repo}/issues/{issue_number}")
    return {"success": True, "issue_data": issue}


def list_issues(args: dict) -> dict:
    repo = args["repo"]
    labels = ",".join(args.get("labels", []))
    state = args.get("state", "open")
    qs = f"?state={state}"
    if labels:
        qs += f"&labels={labels}"
    issues = _request("GET", f"/repos/{repo}/issues{qs}")
    # GitHub returns PRs as issues too; filter
    only_issues = [i for i in issues if "pull_request" not in i]
    return {"success": True, "issues": only_issues}


def list_recent_prs(args: dict) -> dict:
    repo = args["repo"]
    author = args.get("author", "")
    qs = "?state=all&per_page=50"
    prs = _request("GET", f"/repos/{repo}/pulls{qs}")
    if author:
        prs = [p for p in prs if p["user"]["login"] == author]
    if args.get("since"):
        prs = [p for p in prs if p["created_at"] >= args["since"]]
    return {
        "success": True,
        "prs": [
            {
                "number": p["number"],
                "url": p["html_url"],
                "title": p["title"],
                "created_at": p["created_at"],
                "merged_at": p.get("merged_at"),
                "labels": [l["name"] for l in p.get("labels", [])],
            }
            for p in prs
        ],
    }


def push_branch(args: dict) -> dict:
    # This action exists for symmetry; actual git push happens via cli tool.
    # We use this endpoint to verify the branch exists post-push.
    repo = args["repo"]
    branch = args["branch"]
    ref = _request("GET", f"/repos/{repo}/git/ref/heads/{branch}")
    return {"success": True, "branch_sha": ref["object"]["sha"]}


ACTIONS = {
    "open_pr": open_pr,
    "comment": comment,
    "label": label,
    "get_issue": get_issue,
    "list_issues": list_issues,
    "list_recent_prs": list_recent_prs,
    "push_branch": push_branch,
}


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        print(json.dumps({"success": False, "error": "no input"}))
        return
    args = json.loads(raw)
    action = args.get("action")
    if action not in ACTIONS:
        print(json.dumps({"success": False, "error": f"unknown action: {action}"}))
        return
    try:
        result = ACTIONS[action](args)
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    main()
