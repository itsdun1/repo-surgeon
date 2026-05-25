# Org-wide Tech Stack

_This file describes the tech defaults across all repos this Repo Surgeon instance operates on. Edit it to match your organization's stack — the agent reads this at every session._

## Primary languages
- TypeScript / Node.js (services)
- Python (data, scripts, agents)

## Frameworks
- **API**: FastAPI (Python), Express / Hono (Node)
- **Web**: Next.js (App Router)
- **Workers**: Asyncio (Python), BullMQ (Node)

## Data
- **Primary DB**: PostgreSQL 16
- **Cache / queue**: Redis 7
- **Object storage**: S3-compatible (R2 or AWS S3)

## Testing
- **Python**: pytest with `pytest-asyncio` for async tests
- **TypeScript**: Vitest (preferred) or Jest

## CI
- **CI provider**: GitHub Actions
- **Quality gates**: lint + types + tests must pass before merge

## Code style
- **Python**: ruff (lint + format), mypy for types, line length 100
- **TypeScript**: prettier + eslint, strict mode

## Deployment
- **Containers**: Docker
- **Orchestration**: varies per service (k8s for prod, Docker Compose for dev)

---

_Replace any of this with your actual stack. The agent treats this file as ground truth for new repos._
