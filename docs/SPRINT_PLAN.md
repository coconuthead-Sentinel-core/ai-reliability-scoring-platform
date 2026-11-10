# EARP Sprint Plan

Project: Enterprise AI Reliability Platform v1 (EARP)
Release target: v0.3.0
Owner: Shannon Brian Kelley (`coconuthead-Sentinel-core`)
Working branch: `sprint-3/policy-audit-log`
As of: 2026-04-21

---

## Sprint status

| Sprint | Epic | Title | Status |
| --- | --- | --- | --- |
| 0 | baseline | Repo handoff and validation baseline | done |
| 1 | E1 | Evidence Ingestion and Normalization | shim delivered; backlog epic still open |
| 2 | E2 | Reliability Scoring Engine | done |
| 3 | E3 | Policy Gate Evaluation | done on the current branch head |
| 4 | E4 | Dashboard and Reporting | implemented on the current branch head and included in this sync cycle |
| 5 | E5 | Security and Compliance | approval separation, audit ledger, and retention/legal-hold local slices implemented; cloud-only controls are intentionally deferred because Azure credential provisioning is excluded from this cycle |

PR #8 originally represented the exact Sprint 3 delivery branch. The same branch
now carries rolled-forward local Sprint 4 and Sprint 5 work.

The last Azure release-workflow attempt still ran against
`b29da3d9eaeedeae6ad64236c1a59b1961de1e8c`.

---

## Current routing

This project is being routed with an Eisenhower matrix plus the Cognitive Grid
so local product work, release evidence, and Azure blockers stay separated.

### Eisenhower matrix

| Bucket | Items |
| --- | --- |
| Do now | Keep backend and frontend validation green, publish accurate release evidence for the rolled-forward branch head, and sync the branch as the source of truth |
| Schedule next | Rerun GitHub CI on the pushed branch head, decide whether to keep extending PR #8 or cut a new PR after review |
| Delegate / wait | Azure login, active Azure subscription access, GitHub `dev` environment secrets, Key Vault secret population, live FQDN discovery |
| Defer | Live smoke tests and public Azure URLs until Azure deployment credentials exist |

### Cognitive Grid

| Zone | Row family | Active items |
| --- | --- | --- |
| Green | Row 1 / immediate objective | Local Sprint 4 dashboard/reporting build, local Sprint 5 evidence bundle, clean validation |
| Green | Row 5 / active artifacts | `apps/web/src/App.tsx`, `apps/web/src/api.ts`, `enterprise_ai_backend/app/reporting.py`, `docs/SPRINT_PLAN.md`, `docs/go-no-go.md`, `docs/release-evidence.md` |
| Yellow | Row 2 / synthesis | Branch strategy after the rolled-forward local implementation, release evidence refresh |
| Red | Row 10 / archive evidence | CI run results, last Azure workflow result, validation command history, exact blocked secret list |
| Future | Row 13 / backlog horizon | Azure deploy, FQDN capture, live smoke tests, external immutable audit storage, cloud lifecycle retention enforcement, E1 ingestion connectors |

---

## Delivered scope

### Sprint 3 delivered scope

Epic E3 is complete on the current branch head:

1. E3-S1: `POST /policy/evaluate`
   - Composite policy gate with `allow`, `warn`, and `block` outcomes.
   - Per-NIST floor enforcement and threshold override support.

2. E3-S2: policy gate attached to `/assessments`
   - Every assessment row persists `gate_decision` and `gate_reasons`.
   - The gate is computed from the same scores that produce `risk_tier`.

3. E3-S3: policy audit log
   - Every `/policy/evaluate` call is persisted.
   - `GET /policy/history` returns audit history plus trend stats.
   - SQLite compatibility migration upgrades older local databases that
     predate the new `assessments` gate columns.

### Sprint 4 local scope

Epic E4 is now implemented locally on the same branch:

1. `GET /dashboard/summary`
   - Role-aware dashboard payload with KPI cards, epic status, assessment
     posture, reliability score history, and policy history.

2. `GET /reports/executive-summary`
   - Structured executive summary combining the dashboard payload and the
     compliance evidence bundle.

3. `GET /reports/executive-summary.pdf`
   - ReportLab-generated PDF export for review and handoff workflows.

4. React dashboard workspace
   - Release, Security, and Executive views.
   - Local sample-data seeding flow.
   - PDF export button wired to the report endpoint.

### Sprint 5 local scope

Epic E5 now has a local evidence-bundle slice:

1. Compliance evidence bundle
   - Five controls covering auth, CI security scanning, audit traceability,
     release governance, and retention/legal-hold.

2. Release approval workflow
   - Security Lead and Compliance Lead approvals are now separated.
   - Self-approval is blocked for the release requester.

3. Audit ledger
   - Policy evaluations and release approvals are now written into an
     append-only, hash-chained audit ledger.
   - `/audit/history` and `/audit/verify` expose restricted review and
     tamper-detection flows.

4. Retention and legal hold
   - `/compliance/retention/policy` configures the local audit retention window.
   - `/compliance/retention/status` reports eligible and held audit records.
   - `/compliance/legal-holds` and `/compliance/legal-holds/{id}/release`
     manage legal holds for audited entity keys.

5. Outstanding gaps
   - External immutable audit storage, cloud lifecycle retention enforcement, and Azure
     smoke-test completion remain open.

6. Recommended next steps
   - The report endpoints and dashboard now surface the exact local status and
     the remaining blockers.

---

## Validation snapshot

Validated locally on 2026-04-21:

- `python tests/test_backend.py`: pass, 378/378 assertions
- `python -m pytest -q`: pass, 2 tests
- `python -m pip check`: pass
- `python scripts/export_openapi.py`: pass
- `npm run typecheck`: pass
- `npm run build`: pass
- `npm audit --audit-level=moderate`: pass, 0 vulnerabilities
- `az bicep build --file infra/bicep/main.bicep`: pass

Validated on GitHub for the earlier PR #8 branch head:

- `ci-api`: green on Python 3.10, 3.11, 3.12
- `ci-contracts`: green
- `security-scans`: green

Release workflow evidence for `b29da3d`:

- `Build & push images`: success
- `Deploy to Azure Container Apps`: failed at `azure/login@v2`
  because Azure secrets are not configured in the GitHub `dev` environment
- Current repo change: `release.yml` now skips the Azure deployment job when
  those secrets are absent, so cloud credentials are treated as an external
  follow-on instead of a failing repo-completion step

---

## Azure path (excluded from this cycle)

Azure is not blocked by subscription tier. An active Azure Pay-As-You-Go
subscription is sufficient for this project as long as it can create the
required resources and the account has permission to deploy them.

What is intentionally excluded right now:

- `az account show` on this laptop still requires `az login`
- GitHub repository secrets are empty
- GitHub `dev` environment secrets are empty
- no Azure service principal / federated credential values are available for:
  - `AZURE_CLIENT_ID`
  - `AZURE_TENANT_ID`
  - `AZURE_SUBSCRIPTION_ID`
  - `AZURE_MANAGED_IDENTITY_ID`
  - `AZURE_KEY_VAULT_URI`

Once those values exist, the current release workflow is already far enough
along to:

1. build and push API and web images to GHCR,
2. run `azure/arm-deploy@v2` against `infra/bicep/main.bicep`,
3. surface the API and web FQDNs,
4. enable smoke tests against live URLs.

---

## Next execution slice

The next clean move after this sync is:

1. rerun GitHub CI against the current synced branch head,
2. keep Azure deployment excluded until credentials exist,
3. once secrets exist, rerun `release.yml`, collect the API and web FQDNs,
4. run smoke tests against the live URLs.
