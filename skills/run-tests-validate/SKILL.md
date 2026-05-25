---
name: run-tests-validate
description: >
  Detect the target repo's test runner, execute the suite (scoped to changed
  files or full), parse pass/fail, retry on flake. Gates PR creation.
license: Apache-2.0
allowed-tools: [cli, run-tests]
metadata:
  author: repo-surgeon
  version: 1.0.0
  category: validation
  risk_tier: low
---

## Instructions

1. Use the `run-tests` tool to execute the suite. Choose scope based on caller:
   - From `fix-from-issue`: first `scope: file` (the single test that reproduces the bug), then `scope: all` after fix is applied.
   - From `implement-feature`: `scope: all` after each increment.
   - From `propose-refactor`: `scope: changed` (tests touching modified files).
2. Parse the output:
   - Count passed, failed, skipped
   - Capture failure messages, stack traces
   - Detect known flaky patterns (timeout, network, port-in-use)
3. If a failure looks flaky:
   - Retry up to 2 times.
   - If still failing after retries, treat as real.
4. If real failures exist:
   - If failures are in tests YOU added, your implementation is wrong — go back and fix.
   - If failures are in pre-existing tests, your change broke something — revert and reconsider.
5. If tests cannot run at all (missing deps, broken setup):
   - Capture the error from `run-tests.outputs.error`
   - ABORT the workflow with a clear message
   - DO NOT open a PR (RULE 13)
   - Comment on the issue with: "Tests cannot run in this environment. Need: [specific deps/setup]. Aborting."

## Output Format

```json
{
  "runner": "pytest|jest|...",
  "scope": "file|changed|all",
  "passed": int,
  "failed": int,
  "skipped": int,
  "duration_s": float,
  "failures": [{"test": "string", "error": "string", "stack": "string"}],
  "flaky_retried": int,
  "tests_can_run": boolean,
  "abort_reason": "string (if !tests_can_run)"
}
```

## Notes

- If `tests_can_run: false`, the workflow MUST abort. The `enforce_rules.py` hook will block any subsequent `open-pr` call.
- A passing test suite is necessary but not sufficient — also verify your specific change does what was intended.
- For feature PRs, the new tests YOU wrote should be visible in the diff. Reviewers will look for them.
