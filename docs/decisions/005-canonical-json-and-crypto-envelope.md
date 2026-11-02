# Decision Note 005: Canonical JSON and Cryptographic Envelope Specification

- **Status**: Accepted
- **Date**: 2026-11-01
- **Decider**: Lead Engineer / Sanad Core Architecture

## Context
Road A represents the core cryptographic validation pipeline of Sanad. To prevent signature forgery, cross-protocol replay, and hash malleability across disparate runtime platforms, the certificate envelope serialization and signature scheme must conform strictly to RFC standards.

## What Was Chosen
1. **Envelope Model**: W3C Verifiable Credentials Data Model 2.0 with the `eddsa-jcs-2022` cryptosuite:
   - Fixed schema URI: `sanad.cert/1`
   - Unambiguous 80-bit random Base32 certificate ID: `SND-<16 chars>`
   - Salted enrolment hash: `sha256:<salt:enrolment>` to prevent student identity harvesting
2. **Canonicalization**: RFC 8785 (JSON Canonicalization Scheme - JCS)
   - Guarantees byte-for-byte identical output regardless of key insertion order, whitespace, or Unicode normalization.
3. **Domain Separation**:
   - Fixed static byte prefix prepended prior to signing and verification:
     `b"SANAD-CERT-v1\n"`
   - Prevents replaying signatures made for other document types or protocols.
4. **Signature Primitives**:
   - Ed25519 (Edwards-curve Digital Signature Algorithm) via `nacl.signing.SigningKey` and `VerifyKey`.
   - Produces deterministic, non-malleable 64-byte signatures.
5. **Key Identifiers**:
   - `keyId`: The first 8 bytes of the SHA-256 hash of the Ed25519 public key, hex-encoded (16 characters).

## What Was Rejected
- **Standard Python `json.dumps(..., sort_keys=True)`**: Rejected because it does not strictly adhere to RFC 8785 standard number formatting and character escaping rules across different language runtimes.
- **Unprefixed Signing**: Signing raw canonical bytes without domain separation was rejected to protect against cross-context signature replay.

## What Would Change This Decision
Government or university requirements mandating X.509 PAdES (PDF Advanced Electronic Signatures) using RSA 2048/4096-bit hardware HSM tokens.
