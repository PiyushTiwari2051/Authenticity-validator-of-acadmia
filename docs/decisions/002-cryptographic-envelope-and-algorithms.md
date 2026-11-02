# Decision Note 002: Cryptographic Envelope and Signing Primitives

- **Status**: Accepted
- **Date**: 2026-10-31
- **Decider**: Lead Engineer / Sanad Core Architecture

## Context
Road A verification relies on mathematical proof of authenticity and un-tampered provenance. We require an interoperable credential format, deterministic canonical serialization, secure asymmetric signatures, and anti-tamper Merkle batching.

## What Was Chosen
1. **Envelope Model**: W3C Verifiable Credentials Data Model 2.0 structure adapted for `eddsa-jcs-2022` Data Integrity:
   - Fixed schema `sanad.cert/1`.
   - Unguessable certificate ID with >= 80 bits of cryptographic entropy (`SND-<base32>`).
   - Salted SHA-256 hash for student identifiers (`enrolmentNoHash`).
2. **Canonicalization**: RFC 8785 (JSON Canonicalization Scheme - JCS).
3. **Signature Algorithm**: Ed25519 (Edwards-curve Digital Signature Algorithm over Curve25519) using PyNaCl/libsodium.
4. **Domain Separation**: Mandatory static prefix prepended to canonical bytes prior to signing:
   ```text
   SANAD-CERT-v1\n
   ```
5. **Merkle Tree & Anchoring**:
   - Leaf nodes: `SHA-256(0x00 || canonical_bytes)`
   - Interior nodes: `SHA-256(0x01 || left_child || right_child)`
   - RFC 6962 second-preimage attack resistance.
   - Batch roots signed by the platform operator key and chained via `previous_root`.

## What Was Rejected
- **RSA PKCS#1 v1.5 / PSS**: Rejected due to larger signature sizes (256-512 bytes vs 64 bytes for Ed25519) which bloat 2D QR codes and degrade print scanning.
- **Arbitrary JSON string serialization (`json.dumps(..., sort_keys=True)`)**: Python's native JSON serialization does not strictly normalize floating point representations, Unicode escape normalization, or whitespace according to formal cryptographic standards.
- **Raw Undelimited Byte Signing**: Signing canonical JSON without a protocol domain separator opens the system to cross-protocol signature re-use attacks.

## Why
- Ed25519 provides 128-bit security level with extremely fast signing/verification, deterministic signatures (no risk of bad random number generators leaking private keys), and compact 64-byte signatures.
- RFC 8785 guarantees byte-for-byte serialization invariance across Python, JavaScript, Go, and embedded microcontrollers.
- RFC 6962 domain prefixes ensure Merkle trees are structurally immune to leaf/interior node ambiguity attacks.

## What Would Change This Decision
If regulatory compliance with specific Indian e-Sign / PAdES (PDF Advanced Electronic Signatures) standards mandates X.509 RSA hardware security tokens, in which case a dedicated PAdES bridge adapter would be introduced alongside the lightweight Ed25519 core.
