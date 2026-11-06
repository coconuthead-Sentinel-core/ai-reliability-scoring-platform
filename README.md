# Enterprise AI Reliability Platform v1

A platform for scoring and monitoring AI systems against the
NIST AI Risk Management Framework (GOVERN, MAP, MEASURE, MANAGE), with
reliability engineering math, policy gating, audit history, dashboard/reporting
surfaces, and local compliance evidence export.

**Status:** `v0.3.0`. Local checks were re-run on 2026-11-06. Real FastAPI,
real bcrypt + JWT, real scikit-learn `IsolationForest`, and a real SQLAlchemy
persistence layer that runs against either the default local SQLite file or a
hosted Postgres instance. The backend integration suite passes 378/378
assertions, `pytest` passes 2 tests, `pip check` reports no broken
requirements, and the web app typechecks and builds. One check that previously
passed now fails: `npm audit --audit-level=moderate` reports 4 high-severity
advisories in the `vite` dependency chain, and that is not yet remediated. The
exported OpenAPI contract still matches the running app. Azure credential
provisioning remains an external prerequisite intentionally excluded from the
current work cycle.

## Project Identity

The canonical public name for this repo is **Enterprise AI Reliability Platform v1**.
Approved short form: `EARP`.
Use `EARP` only for this project.

## Monorepo layout

```text
enterprise-ai-reliability-platform-v1/
|- api/                   Legacy signpost -> enterprise_ai_backend/
|- apps/
|  |- api/                 Signpost -> enterprise_ai_backend/
|  `- web/                 React 18 + TypeScript + Vite dashboard UI
|- enterprise_ai_backend/  FastAPI app, persistence, reporting, tests
|- libs/
|  |- schemas/             OpenAPI 3.1 contract exported from FastAPI
|  `- policy/              NIST AI RMF scoring policy
|- infra/
|  |- docker/              Local compose stack
|  `- bicep/               Azure Container Apps deployment
|- src/                    Second FastAPI app: in-memory demo API
|- docs/                   Engineering and release docs
`- ...                     SDLC, architecture, risk, and compliance folders
```

The `enterprise_ai_backend/` folder is the database-backed API tree described
by the Quickstart and the OpenAPI contract below.

The repository also contains a second, self-contained FastAPI application in
`src/`, started with `uvicorn src.main:app`. It keeps its evidence, scoring,
policy, and audit services in memory, preloads three mock evaluation runs at
startup, and declares its own `requirements.txt` (no SQLAlchemy, no bcrypt). It
shares no code with `enterprise_ai_backend/`. Treat the two as separate
applications; whether `src/` is retained, merged, or retired is an open
decision and is not settled by this document.

Both `apps/api/` and `api/` are signpost folders kept for navigation and
backward-compatible repo wayfinding.

## Quickstart

### Backend

```bash
cd enterprise_ai_backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
python tests/test_backend.py
```

Key local endpoints:

- `/docs`
- `/policy/evaluate`
- `/policy/history`
- `/audit/history`
- `/audit/verify`
- `/compliance/retention/policy`
- `/compliance/retention/status`
- `/compliance/legal-holds`
- `/release/approvals/current`
- `/release/approvals/request`
- `/dashboard/summary`
- `/reports/executive-summary`
- `/reports/executive-summary.pdf`

### Frontend

```bash
cd apps/web
npm install
npm run dev
```

The local web app opens at `http://127.0.0.1:5173` and expects the backend at
`http://127.0.0.1:8000`.

## Current product surface

- Reliability scoring with weighted composite output and NIST breakdown
- Policy evaluation with allow/warn/block decisions and hash-chained audit history
- Release approval workflow with separated Security Lead and Compliance Lead sign-off
- Retention policy and legal-hold controls for audited records
- Authenticated NIST AI RMF assessments with persisted gate outcomes
- Dashboard workspace with Release, Security, and Executive views
- JSON and PDF executive summary export
- Local compliance evidence bundle with control coverage, gaps, and next steps

## Validation snapshot

Every line below was observed on 2026-11-06, in a worktree at commit `aa7c1e0`
with no code changes applied (only this README differs), using Python 3.13.14,
Node 24.15.0, and npm 11.12.1 on Windows 11. Nothing in this list is carried
over from the earlier 2026-04-21 run.

- `python tests/test_backend.py`, run from `enterprise_ai_backend/`: pass,
  378/378 assertions, exit code 0
- `python -m pytest -q`, run from the repo root: pass, 2 tests, plus 2
  `DeprecationWarning`s for FastAPI's `on_event` startup hook
- `python -m pip check`: pass, no broken requirements
- `python scripts/export_openapi.py`, run from `enterprise_ai_backend/`: pass;
  the regenerated `libs/schemas/openapi.json` matches the committed contract
  apart from line endings
- `npm run typecheck`, run in `apps/web`: pass
- `npm run build`, run in `apps/web`: pass, 16 modules transformed, 158.04 kB
  JS bundle
- `az bicep build --file infra/bicep/main.bicep`: pass
- `npm audit --audit-level=moderate`, run in `apps/web`: **fail** - 4 high
  severity advisories, all in the `vite` dependency chain. The previous
  "pass, 0 vulnerabilities" result dated 2026-04-21 no longer holds. Not
  remediated as of this commit.

The suite exercises SQLite, which is the default local backend. No test run
recorded here was executed against Postgres, so Postgres support is verified
only at the configuration level, not by a passing test.

## CI/CD

GitHub Actions workflows:

1. `ci-api.yml`
2. `ci-web.yml`
3. `ci-contracts.yml`
4. `security-scans.yml`
5. `release.yml`

As of 2026-11-05, `ci-api`, `ci-web`, and `ci-contracts` are green on `main`
(latest run 2026-11-05, commit `aa7c1e0`). The most recent recorded run of
`security-scans.yml` was 2026-06-28; GitHub suspends scheduled workflows on
inactive repositories, so treat that scan coverage as lapsed until a run is
observed.

The release workflow always builds and pushes GHCR images. It only runs the
Azure deployment job when the selected environment exposes the required Azure
secrets; otherwise the Azure job is skipped and credential provisioning remains
an external follow-on task.

## Deployment

`enterprise_ai_backend/app/config.py` rewrites `postgres://` and
`postgresql://` URLs to the `postgresql+psycopg` dialect, and
`psycopg[binary]>=3.1` is now a required dependency rather than a
commented-out one, so the backend runs against hosted Postgres as well as the
default local SQLite file. The in-code comment names Railway and Heroku as the
intended hosts.

An Azure Pay-As-You-Go subscription remains sufficient for the bicep path.
Credential setup is external to the repo and intentionally excluded from the
current work cycle; live deployment can resume once those values are
available.

## More docs

- `docs/README.md`
- `docs/SPRINT_PLAN.md`
- `docs/go-no-go.md`
- `docs/release-evidence.md`
