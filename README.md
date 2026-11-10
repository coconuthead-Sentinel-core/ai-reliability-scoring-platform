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
requirements, the web app typechecks and builds, and
`npm audit --audit-level=moderate` reports 0 vulnerabilities following the
`vite` 8.3.6 dependency upgrade. The exported OpenAPI contract still matches
the running app. Azure credential provisioning remains an external
prerequisite intentionally excluded from the current work cycle.

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
|- docs/                   Engineering and release docs
`- ...                     SDLC, architecture, risk, and compliance folders
```

The `enterprise_ai_backend/` folder is the database-backed API tree described
by the Quickstart and the OpenAPI contract below.

It is the only FastAPI application in the repository. A second, unwired
prototype under `src/` was retired on 2026-11-10; it remains in history at
`ae40bd5` if its mock fixtures are ever wanted.

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

Every line below was observed on 2026-11-06, using Python 3.13.14, Node
24.15.0, and npm 11.12.1 on Windows 11. The Python lines were re-run against
this branch in a clean virtualenv built from
`enterprise_ai_backend/requirements.txt` alone, so nothing could fall back on
a package the file no longer declares. The `apps/web` and `infra/` lines were
observed earlier the same day at `60a7f9d`; this branch does not touch either
tree. No line is carried over from the 2026-04-21 run.

- `python tests/test_backend.py`, run from `enterprise_ai_backend/`: pass,
  378/378 assertions, exit code 0
- `python -m pytest -q`, run from the repo root: pass, 2 tests, plus 3
  warnings - two `DeprecationWarning`s for FastAPI's `on_event` startup hook
  and one `StarletteDeprecationWarning` about `httpx` in the test client,
  none of them related to the JWT change
- `python -m pip check`: pass, no broken requirements
- `pip-audit -r enterprise_ai_backend/requirements.txt`: pass, no known
  vulnerabilities
- `python scripts/export_openapi.py`, run from `enterprise_ai_backend/`: pass;
  the regenerated `libs/schemas/openapi.json` matches the committed contract
  apart from line endings
- `npm run typecheck`, run in `apps/web`: pass
- `npm run build`, run in `apps/web`: pass on vite 8.3.6, 16 modules
  transformed, 157.96 kB JS bundle
- `az bicep build --file infra/bicep/main.bicep`: pass
- `npm audit --audit-level=moderate`, run in `apps/web`: pass, 0
  vulnerabilities, re-confirmed after deleting `node_modules` and running
  `npm ci` from the updated lockfile

The backend dependency audit also failed earlier on 2026-11-06, reporting
PYSEC-2026-4298 in `python-jose` 3.5.0 and PYSEC-2026-1325 in its `ecdsa`
0.19.2 dependency. Neither had a fixed release upstream, so JWT handling was
moved to PyJWT and `python-jose` was dropped; see the CHANGELOG. Token format,
claims, and the HS256 default are unchanged.

Earlier on 2026-11-06 the web audit failed with 4 high-severity advisories, all
within the `vite` dependency chain (`vite` -> `postcss` -> `nanoid` and
`source-map-js`). They were cleared by moving `vite` from 8.0.8 to 8.3.6,
which brings `postcss` 8.5.32, `nanoid` 3.3.20, and `source-map-js` 1.2.2. The
upgrade stayed inside the existing `^8` major; `typecheck` and `build` both
pass on it. The declared floor in `apps/web/package.json` was raised to
`^8.3.6` so a fresh resolve cannot land back on a vulnerable 8.0.x.

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
