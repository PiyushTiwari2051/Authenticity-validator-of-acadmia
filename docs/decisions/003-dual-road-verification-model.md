# Decision Note 003: Dual-Road Verification Model and Verdict Semantics

- **Status**: Accepted
- **Date**: 2026-10-31
- **Decider**: Lead Engineer / Sanad Core Architecture

## Context
Verifiers receive credentials through two fundamentally distinct media:
1. Native digital credentials issued directly by participating institutions.
2. Legacy physical certificates, scans, photocopies, or mobile camera photographs.
A common failure mode in academic verification systems is presenting a single blended confidence score (e.g. "98.4% Authentic") that conflates mathematical cryptographic proof with heuristic image processing.

## What Was Chosen
Strict computational, pipeline, and linguistic separation into two non-overlapping roads:

### Road A: Issuer-Signed Cryptographic Path
- **Nature**: Deterministic, mathematical proof.
- **Verdict Vocabulary (Fixed)**:
  - `VERIFIED_ISSUER_SIGNED`: Signature valid, issuer approved, key active/anchored, not revoked, batch anchored.
  - `VERIFIED_PENDING_ANCHOR`: Cryptographically valid, but current Merkle batch has not yet sealed.
  - `REVOKED`: Valid signature, but explicitly revoked by the issuer.
  - `INVALID_SIGNATURE`: Cryptographic verification failed; payload tampered or key mismatch.
  - `ISSUER_NOT_APPROVED`: Signing key belongs to an unapproved or suspended institution.
  - `KEY_WINDOW_UNSAFE`: Key marked compromised prior to batch anchoring time.
  - `NOT_FOUND`: Identifier not recognized in platform registry.

### Road B: Legacy Scanned Physical Path
- **Nature**: Heuristic, probabilistic, and explicitly advisory.
- **Verdict Vocabulary (Fixed)**:
  - `CONSISTENT_WITH_REGISTRY`: OCR extracted fields match institution historical registry record. Not proof paper is genuine.
  - `NEEDS_REVIEW`: Ambiguous OCR, low scan quality, or weak forensic divergence requiring registrar confirmation.
  - `LIKELY_ALTERED`: Contradiction with institution database, or multiple independent forensic anomalies detected.
  - `CANNOT_VERIFY`: No matching registry record, or scan failed quality gate (severe blur, resolution < 150 DPI, excessive skew).

## What Was Rejected
- **Unified "Authenticity Score"**: e.g., combining OCR confidence and signature checks into a single percentage.
- **Claiming "100% Authentic" on Road B**: Scanned images can never be proven authentic by software alone, as an original physical paper could be forged with authentic details or a genuine scan could be modified before printing.

## Why
1. **Intellectual Honesty**: Conflating heuristic computer vision with digital signatures invites immediate, fatal criticism from evaluators and security analysts.
2. **Defensible Explanations**: A verifier is given exact reasoning (e.g., "Registration number matched registry record, but Copy-Move analysis identified duplicated stamp artifact in seal area").
3. **Actionable Outcomes**: When Road B yields `NEEDS_REVIEW` or `CANNOT_VERIFY`, the system offers a formal asynchronous confirmation request workflow to the registrar rather than a deceptive pass/fail verdict.

## What Would Change This Decision
Nothing within the lifetime of this architecture. Even if deep learning models achieve 99.9% detection accuracy on synthetic benchmarks, Road B will remain designated as probabilistic advisory analysis.
