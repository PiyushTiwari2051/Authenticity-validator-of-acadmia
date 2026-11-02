# Decision Note 001: Modular Monolith Architecture

- **Status**: Accepted
- **Date**: 2026-10-31
- **Decider**: Lead Engineer / Sanad Core Architecture

## Context
Project Sanad (SIH25029) requires an API service, background asynchronous workers for OCR/forensics, relational persistence with strict ACID guarantees, object storage for certificate artifacts, and an accessible frontend for public verifiers and academic institutions. A core architectural question is whether to deploy microservices across business domains or organize as a modular monolith.

## What Was Chosen
A **modular monolith** topology:
- Single FastAPI (Python) backend organized strictly into clean internal domain modules:
  - `auth`: Identity, RBAC, TOTP, session families.
  - `institutions`: Onboarding, lifecycle, key management.
  - `issuance`: Certificate issuance, canonicalization, signing, and PDF generation.
  - `verify`: Dual-pipeline verification engine (Road A & Road B).
  - `registry`: Historical graduate records for Road B matching.
  - `audit`: Append-only, hash-chained audit logging.
  - `analytics`: Honest aggregations and platform telemetry.
- Single worker service running against Redis for heavy, long-running jobs (image rasterization, OCR, forensic analysis, Merkle tree batching).
- PostgreSQL 16 as the sole relational database, enforcing foreign keys, unique constraints, and append-only trigger rules.
- Next.js (TypeScript) for the frontend user interface, leveraging server rendering for lightweight mobile public verification.
- MinIO for local S3-compatible object storage.

## What Was Rejected
- **Distributed Microservices**: Splitting the platform into separate deployable microservices (e.g. Auth Service, Issuance Service, Verification Service, Forensic Service) communicating via gRPC/REST.
- **Polyglot API Layer**: Writing the API in Go/Rust and invoking Python as a separate sidecar for OCR and computer vision.
- **Document / NoSQL Stores**: Storing certificate records or audit entries in MongoDB or DynamoDB.

## Why
1. **Explainability & Viva Defensibility**: In evaluation and jury viva settings, a distributed microservices setup introduces unnecessary complexity (distributed transactions, network failure modes, contract synchronization) that obscures the core cryptography and forensics.
2. **Type Safety & Schema Reuse**: FastAPI with Pydantic v2 allows sharing exact data structures between the HTTP API, background workers, and evaluation test harnesses.
3. **Data Integrity**: Relational constraints and transactional rollback prevent orphan certificates or unsynchronized batch roots.
4. **Developer Experience**: A single `docker compose up` brings up the exact operational system on any standard machine.

## What Would Change This Decision
If production measurements demonstrate that heavy forensic CV/OCR operations create severe memory or CPU starvation that cannot be mitigated by Redis worker process isolation and container resource limits.
