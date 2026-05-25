# Team Conventions

_Code review norms, PR culture, and naming rules that apply across the org._

## PR conventions
- Squash-merge by default. Branch deleted after merge.
- One concern per PR (the agent already enforces this — RULE 11).
- PR description must explain *why*, not just *what*.
- Breaking changes require a `BREAKING CHANGE:` footer in the commit message.

## Branch naming
- Feature branches: `feat/<short-description>` or `feature/<short-description>`
- Bug fix branches: `fix/<short-description>`
- Refactor branches: `refactor/<short-description>`
- Surgeon branches: `surgeon/<session-id>` (do not interfere)

## Commit messages
- Conventional Commits format preferred: `feat(scope): description`, `fix(scope): description`, etc.
- First line under 70 chars.
- Body wraps at 72 chars.

## Code review
- At least one human approval required before merge.
- Surgeon PRs ARE NOT exempt from human review.
- Maintainer can request `@security-team` review for anything touching auth/crypto.

## Documentation
- New public APIs require a docstring/JSDoc.
- Changes to public APIs require a CHANGELOG entry.
- README must stay current — outdated install instructions are a known smell.

---

_Edit to match your team's actual norms. The agent uses this as the default when no per-repo override exists._
