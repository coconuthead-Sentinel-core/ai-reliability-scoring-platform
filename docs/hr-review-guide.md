# HR Review Guide

This guide is written for a hiring manager or technical reviewer who wants to verify that EARP is a working software project, not a static mockup.

## What To Review

- API: FastAPI backend with authentication, reliability math, NIST AI RMF assessments, SHA-256 hashing, and scikit-learn IsolationForest anomaly detection.
- UI: React 18 + TypeScript + Vite frontend calling the real API.
- Contracts: OpenAPI 3.1 schema exported from the running FastAPI app.
- Delivery: Dockerfiles, Docker Compose, GitHub Actions, and Azure Container Apps Bicep.

## Local Terminal Test

```powershell
cd "C:\Users\sbrya\OneDrive\Desktop\enterprise-ai-reliability-platform-v1\enterprise-ai-reliability-platform-v1\enterprise_ai_backend"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe test_backend.py
```

Expected result: the script prints `FULL BUILD TESTS PASSED - REAL AUTH, REAL ML, REAL NUMBERS`.

## Live API Test

After deployment, set `EARP_API_URL` to the deployed API URL recorded in `docs/release-evidence.md`, then run:

```powershell
cd "C:\Users\sbrya\OneDrive\Desktop\enterprise-ai-reliability-platform-v1\enterprise-ai-reliability-platform-v1\enterprise_ai_backend"
.\.venv\Scripts\python.exe scripts\demo_flow.py --base-url $env:EARP_API_URL
```

The script registers a real user, logs in, computes real reliability metrics, creates a NIST AI RMF assessment, and runs anomaly detection against stored reliability history.

## Evidence That Numbers Are Real

- Reliability uses `availability = MTBF / (MTBF + MTTR)`.
- Reliability uses `reliability = exp(-mission_time / MTBF)`.
- Hashing uses Python `hashlib.sha256`.
- Passwords use the `bcrypt` package directly, not through `passlib`.
- Tokens use signed JWT through `PyJWT`.
- Anomaly detection uses scikit-learn `IsolationForest`.

## Current Public URL

Status: pending Azure authentication and deployment. The local build is validated; the public web URL and API URL must be recorded here immediately after Azure deployment succeeds.
