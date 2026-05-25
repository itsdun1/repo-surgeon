#!/usr/bin/env python3
"""read-issue tool — fetches a GitHub issue with comments via REST API."""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request


GITHUB_API = "https://api.github.com"
LINKED_PR_RE = re.compile(r"#(\d+)")


def _request(path: str) -> object:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN env not set")
    url = f"{GITHUB_API}{path}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "repo-surgeon")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub API {e.code}: {e.read().decode()[:200]}") from e


def main():
    raw = sys.stdin.read()
    args = json.loads(raw)
    repo = args["repo"]
    num = args["issue_number"]
    try:
        issue = _request(f"/repos/{repo}/issues/{num}")
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        return

    out = {
        "title": issue["title"],
        "body": issue.get("body") or "",
        "labels": [l["name"] for l in issue.get("labels", [])],
        "author": issue["user"]["login"],
        "state": issue["state"],
        "created_at": issue["created_at"],
        "updated_at": issue["updated_at"],
        "comments": [],
        "linked_prs": [],
    }

    # Comments
    if args.get("include_comments", True) and issue.get("comments", 0) > 0:
        try:
            comments = _request(f"/repos/{repo}/issues/{num}/comments")
            max_c = args.get("max_comments", 50)
            out["comments"] = [
                {
                    "author": c["user"]["login"],
                    "body": c["body"],
                    "created_at": c["created_at"],
                }
                for c in (comments or [])[:max_c]
            ]
        except Exception:
            pass

    # Linked PRs: extract issue numbers mentioned in body + comments, check if any are PRs
    bodies = [out["body"]] + [c["body"] for c in out["comments"]]
    candidates = set()
    for b in bodies:
        candidates.update(int(x) for x in LINKED_PR_RE.findall(b or ""))
    for cand in list(candidates)[:5]:  # limit roundtrips
        try:
            maybe = _request(f"/repos/{repo}/pulls/{cand}")
            out["linked_prs"].append({"number": cand, "url": maybe["html_url"], "state": maybe["state"]})
        except Exception:
            continue

    print(json.dumps(out))


if __name__ == "__main__":
    main()
