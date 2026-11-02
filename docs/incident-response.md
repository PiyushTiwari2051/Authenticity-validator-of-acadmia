# Incident Response Plan

Date: 2026-10-31
Scope: Protocol handling for cryptographic key compromises, data breaches, and erroneous/fraudulent credential issuances.

---

## 1. Key Compromise Incident Protocol

In the event that an institution's private signing key is suspected or confirmed compromised:

1. **Immediate Notification & Isolation**:
   - The institution administrator or platform security team triggers `POST /api/v1/institutions/{id}/keys/{keyId}/compromise`.
   - The request requires two-factor authentication (TOTP) and records a precise `compromisedFrom` ISO 8601 timestamp.
2. **Key State Transition**:
   - Key status is atomically updated to `compromised` in PostgreSQL.
   - An immutable audit log entry is written and added to the pending Merkle batch.
   - The updated public key status is propagated to the public transparency log.
3. **Validity Determination**:
   - **Pre-compromise Certificates**: Any certificate whose containing Merkle batch was anchored **prior** to `compromisedFrom` remains trusted (`VERIFIED_ISSUER_SIGNED`).
   - **Post-compromise Certificates**: Any certificate signed by the compromised key with an anchor time after `compromisedFrom` (or pending anchor) evaluates immediately to `KEY_WINDOW_UNSAFE`.
4. **Key Rotation**:
   - A replacement key pair is generated and published at the institution's canonical URL (`/.well-known/sanad-keys.json`).
   - Platform admin re-verifies domain key binding.

---

## 2. Erroneous or Fraudulent Issuance Protocol

If a legitimate key was used by an operator or registrar to issue an inaccurate or fraudulent certificate:

1. **Atomic Revocation**:
   - The institution registrar or operator executes `POST /api/v1/certificates/{id}/revoke`.
   - A mandatory reason code must be selected:
     - `ISSUED_IN_ERROR`: Typographical or data entry error.
     - `REPLACED_BY_CORRECTION`: Certificate superseded by a corrected reissuance.
     - `DEGREE_WITHDRAWN`: Academic disqualification or disciplinary action.
     - `FRAUD_FOUND`: Unauthorized issuance or falsified academic record.
2. **Cryptographic Statement**:
   - The revocation statement is canonicalized, signed by the institution key, stored in the append-only `revocations` table, and scheduled for leaf inclusion in the next Merkle batch.
3. **Public Exposure**:
   - Subsequent verifications immediately return `REVOKED`, detailing the revocation timestamp and reason code.
   - The signed revocation list at `/.well-known/sanad/revocations/{institutionId}.json` is refreshed.

---

## 3. Data Leak & DPDP Compliance Protocol

1. **Assessment & Containment**:
   - Identify the source of the leak (API exposure, object storage misconfiguration, or unauthorized database access).
   - Invalidate exposed sessions and rotate database credentials immediately.
2. **DPDP Section 8 Notification**:
   - In accordance with the Digital Personal Data Protection Act 2023, notify the Data Protection Board of India and affected data principals with:
     - Nature and extent of personal data exposed.
     - Immediate mitigation measures taken.
     - Recommended protective steps for holders.
3. **Log Sanitization Verification**:
   - Audit system logs to ensure zero plain-text passwords, TOTP secrets, or personal demographic fields were written to application log streams.
