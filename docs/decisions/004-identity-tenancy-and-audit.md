# Decision Note 004: Identity, Tenancy, and Audit Integrity

- **Status**: Accepted
- **Date**: 2026-10-31
- **Decider**: Lead Engineer / Sanad Core Architecture

## Context
Phase 1 implements user identities, tenant isolation across institutions, secure credential hashing (Argon2id), mandatory multi-factor authentication (TOTP) for administrative and staff roles, refresh token rotation with reuse detection, and a cryptographically tamper-evident, append-only audit log.

## What Was Chosen
1. **Password Hashing**: Argon2id via `argon2-cffi` adhering to OWASP recommendations (time cost = 3 iterations, memory cost = 65,536 KiB, parallelism = 4 threads).
2. **Two-Factor Authentication**: Mandatory RFC 6238 TOTP for `platform_admin`, `institution_admin`, and `operator` roles. TOTP secrets encrypted at rest using AES-256-GCM under `SANAD_KEK`.
3. **Session Management**: Short-lived JWT access tokens (15 minutes) and rotating refresh tokens (7 days) stored as salted SHA-256 hashes in PostgreSQL. Any reuse of an already-rotated refresh token revokes the entire session family immediately.
4. **Tenant Isolation**: Institution data access is enforced at the data layer by scoping all institution queries with `institution_id` matching the authenticated operator's tenant context. Cross-tenant reads and mutations raise 403 Forbidden.
5. **Hash-Chained Audit Trail**:
   - Append-only `audit_log` table.
   - Database trigger / application rules rejecting `UPDATE` and `DELETE`.
   - Each audit entry computes `row_hash = SHA-256(prev_hash || actor_id || actor_role || action || object_type || object_id || ip_hash || detail_json || created_at)`.
   - A dedicated audit verification function allows any auditor to verify that the chain is unbroken.

## What Was Rejected
- **bcrypt or PBKDF2**: Argon2id is standard for new systems due to memory-hardness against GPU/ASIC cracking.
- **Client-Side Stored JWTs in localStorage**: Storing tokens in localStorage leaves sessions open to XSS token exfiltration. HttpOnly, SameSite cookies are mandated.
- **Unchained Audit Logs**: Standard audit tables can be mutated silently by malicious database operators; hash-chaining prevents silent alteration or row deletion.

## Why
Defensible, enterprise-grade multi-tenancy ensures that no registrar can see or manipulate another institution's credentials, while the cryptographic hash-chained audit log guarantees post-issuance accountability.

## What Would Change This Decision
Government or university federation mandates requiring SAML 2.0 / OpenID Connect single sign-on (SSO) with university identity providers.
