# Deploy Process

_How code reaches production across our repos._

## Default flow
1. PR opened → CI runs lint/types/tests
2. Human review + approval
3. Merge to default branch (squash)
4. CI deploys to staging on every merge
5. Production deploy is manual (tagged release `v*`)

## Repo-specific overrides
If a target repo has a different process, document it in `memory/repos/<repo>/conventions.md` under a `## Deploy` heading.

## What the agent never does
- Trigger a deploy
- Modify CI config (forbidden via RULE 1)
- Touch infra-as-code (Terraform, Helm, etc.)

If a fix would require any of the above, the agent aborts and comments on the issue with what's needed manually.
