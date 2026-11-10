# Portfolio Brief - Enterprise AI Reliability Platform v1

> **One-page recruiter overview.** Architecture detail in [`../README.md`](../README.md). Polish-pass changelog in [`../POLISH_NOTES.md`](../POLISH_NOTES.md).

## TL;DR

**Production-grade platform** for scoring and monitoring AI systems against the NIST AI Risk Management Framework (GOVERN / MAP / MEASURE / MANAGE). Real FastAPI, real bcrypt plus JWT, real SQLite, real scikit-learn `IsolationForest`, OpenAPI 3.1 contract, React 18 plus TypeScript plus Vite dashboard, Docker compose for local, and Azure bicep for deployment. **378/378 integration assertions passing on v0.3.0** (validated 2026-04-21).

## Naming

Canonical public name: **Enterprise AI Reliability Platform v1**.
Approved short form: `EARP`.
Do not expand `EARP` into unrelated internal folder labels.

## Role demonstrated

**AI Reliability Engineer / AI Compliance Architect / Senior Backend Engineer** - NIST AI RMF compliance implementation, anomaly-detection ML integration, and full-stack reliability engineering with policy gating and audit history.

## What this project demonstrates

| Capability | Evidence |
|---|---|
| **NIST AI RMF compliance implementation** | `libs/policy/` with explicit GOVERN / MAP / MEASURE / MANAGE scoring policy |
| **Production test discipline** | **378 / 378 integration assertions passing** on v0.3.0 |
| **Real ML integration** | scikit-learn `IsolationForest` running anomaly detection |
| **Real auth** | bcrypt for password hashing plus JWT session tokens |
| **Real persistence** | SQLite with documented schema |
| **OpenAPI contract** | `libs/schemas/` exports OpenAPI 3.1 directly from FastAPI |
| **Modern frontend** | React 18 plus TypeScript plus Vite dashboard |
| **Container deployment** | `infra/docker/` for local plus `infra/bicep/` for Azure Container Apps |
| **Governance artifacts** | ADR, privacy, compliance, incident response, and release-readiness folders are present |

## Honest scope statement

Status per the README: v0.3.0, full local build validated 2026-04-21. Repo docs, contracts, and release packaging are current. Azure credential provisioning remains an external prerequisite intentionally excluded from the current work cycle.

## Portfolio positioning

| Other portfolio pieces | This project |
|---|---|
| Sentinel-of-sentinel-s-Forge | Production patterns plus Stripe billing |
| Sentinel Prime Network | Three-tier MVP scaffold; internal stack label `Forge-Stack-A1` |
| Quantum Nexus Forge | Proof-of-concept orchestration MVP |
| Sovereign Forge | Multi-platform gateway |
| Sentinel Forge Cognitive AI Orchestrator | Adaptive cognition and accessibility-first orchestration |

This is the lead artifact for senior AI reliability and compliance role applications.

## Author

**Shannon Brian Kelley** - Healthcare CNA -> AI Systems Developer career transition.  
Built in collaboration with Claude AI (Anthropic).
