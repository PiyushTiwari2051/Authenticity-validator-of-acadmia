"""Verification Engine Core:
Builds verify(input) -> VerificationResult with Road A and Road B pipelines.
Enforces the exact fixed vocabulary mandated by Section 8.1.
"""

from enum import Enum
import hashlib
import time
from typing import Any, Optional
import uuid
from pydantic import BaseModel, Field

from backend.app.modules.crypto.canonical import canonicalize_json
from backend.app.modules.crypto.signer import verify_signature, DOMAIN_PREFIX


class VerdictCode(str, Enum):
    # Road A (Digital)
    VERIFIED_ISSUER_SIGNED = "VERIFIED_ISSUER_SIGNED"
    VERIFIED_PENDING_ANCHOR = "VERIFIED_PENDING_ANCHOR"
    REVOKED = "REVOKED"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"
    ISSUER_NOT_APPROVED = "ISSUER_NOT_APPROVED"
    KEY_WINDOW_UNSAFE = "KEY_WINDOW_UNSAFE"
    NOT_FOUND = "NOT_FOUND"

    # Road B (Scanned Paper)
    CONSISTENT_WITH_REGISTRY = "CONSISTENT_WITH_REGISTRY"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    LIKELY_ALTERED = "LIKELY_ALTERED"
    CANNOT_VERIFY = "CANNOT_VERIFY"


class FindingOutcome(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIPPED = "skipped"


class VerificationFindingItem(BaseModel):
    check: str
    outcome: FindingOutcome
    score: Optional[float] = None
    detail: str


class CertificatePublicSummary(BaseModel):
    id: str
    holderName: str
    title: str
    programme: str
    issuedOn: str
    institutionName: Optional[str] = None


class VerificationResult(BaseModel):
    road: str  # "A" or "B"
    verdict: VerdictCode
    summary: str
    certificate: Optional[CertificatePublicSummary] = None
    findings: list[VerificationFindingItem]
    anchor: Optional[dict[str, Any]] = None
    durationMs: float


def verify_road_a_pipeline(
    cert_record: Optional[Any],
    inst_record: Optional[Any],
    key_record: Optional[Any],
    revocation_record: Optional[Any],
    batch_record: Optional[Any],
    inclusion_proof: Optional[list[dict[str, str]]] = None,
) -> VerificationResult:
    """Execute Road A 9-step verification pipeline in strict order."""
    start_time = time.perf_counter()
    findings: list[VerificationFindingItem] = []

    # Step 2: Unknown ID check
    if not cert_record:
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return VerificationResult(
            road="A",
            verdict=VerdictCode.NOT_FOUND,
            summary="No such certificate ID in this system.",
            findings=[
                VerificationFindingItem(
                    check="certificate_lookup",
                    outcome=FindingOutcome.FAIL,
                    detail="Certificate ID does not exist in platform database."
                )
            ],
            durationMs=duration_ms
        )

    # Step 3: Canonical bytes recomputation
    payload_json = cert_record.payload_json
    recomputed_canonical = canonicalize_json(payload_json)
    if recomputed_canonical != cert_record.canonical_payload:
        findings.append(VerificationFindingItem(
            check="canonical_integrity",
            outcome=FindingOutcome.FAIL,
            detail="Payload bytes do not match canonical database storage."
        ))
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return VerificationResult(
            road="A",
            verdict=VerdictCode.INVALID_SIGNATURE,
            summary="The content or signature does not match; do not trust this document.",
            findings=findings,
            durationMs=duration_ms
        )
    findings.append(VerificationFindingItem(
        check="canonical_integrity",
        outcome=FindingOutcome.PASS,
        detail="Canonical JSON bytes match stored payload."
    ))

    # Step 4: Verify Ed25519 signature
    if not key_record or not verify_signature(key_record.public_key, recomputed_canonical, cert_record.signature):
        findings.append(VerificationFindingItem(
            check="signature",
            outcome=FindingOutcome.FAIL,
            detail=f"Cryptographic signature does not match key {cert_record.key_id}."
        ))
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return VerificationResult(
            road="A",
            verdict=VerdictCode.INVALID_SIGNATURE,
            summary="The content or signature does not match; do not trust this document.",
            findings=findings,
            durationMs=duration_ms
        )
    findings.append(VerificationFindingItem(
        check="signature",
        outcome=FindingOutcome.PASS,
        detail=f"Ed25519 signature verified with key {cert_record.key_id}."
    ))

    # Step 5: Check institution status & key status
    if not inst_record or inst_record.status != "approved":
        findings.append(VerificationFindingItem(
            check="issuer_status",
            outcome=FindingOutcome.FAIL,
            detail=f"Institution status is '{getattr(inst_record, 'status', 'unknown')}', not approved."
        ))
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return VerificationResult(
            road="A",
            verdict=VerdictCode.ISSUER_NOT_APPROVED,
            summary="The signing institution is not approved, or is suspended.",
            findings=findings,
            durationMs=duration_ms
        )
    findings.append(VerificationFindingItem(
        check="issuer_status",
        outcome=FindingOutcome.PASS,
        detail=f"Institution approved on {inst_record.approved_at or 'record'}."
    ))

    # Key compromise check
    if key_record.status == "compromised":
        if not batch_record or not batch_record.anchored_at or (key_record.compromised_from and batch_record.anchored_at > key_record.compromised_from):
            findings.append(VerificationFindingItem(
                check="key_integrity",
                outcome=FindingOutcome.FAIL,
                detail=f"Key was marked compromised at {key_record.compromised_from} without pre-compromise anchoring."
            ))
            duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            return VerificationResult(
                road="A",
                verdict=VerdictCode.KEY_WINDOW_UNSAFE,
                summary="Signed by a key later marked compromised, with no anchor proof from before that time.",
                findings=findings,
                durationMs=duration_ms
            )

    # Step 6: Check revocation
    if revocation_record or cert_record.status == "revoked":
        reason = getattr(revocation_record, "reason_code", "REVOKED")
        rev_date = getattr(revocation_record, "revoked_at", "recorded")
        findings.append(VerificationFindingItem(
            check="revocation",
            outcome=FindingOutcome.FAIL,
            detail=f"Certificate was revoked: reason {reason} on {rev_date}."
        ))
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return VerificationResult(
            road="A",
            verdict=VerdictCode.REVOKED,
            summary=f"The institution withdrew it ({reason}); revoked on {rev_date}.",
            findings=findings,
            durationMs=duration_ms
        )
    findings.append(VerificationFindingItem(
        check="revocation",
        outcome=FindingOutcome.PASS,
        detail="No revocation recorded; live registry clear."
    ))

    # Step 7: Batch anchoring check
    if not batch_record or not batch_record.anchored_at:
        findings.append(VerificationFindingItem(
            check="inclusion",
            outcome=FindingOutcome.WARN,
            detail="In current open batch; batch has not closed yet."
        ))
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return VerificationResult(
            road="A",
            verdict=VerdictCode.VERIFIED_PENDING_ANCHOR,
            summary=f"Signed by {inst_record.name}. Not revoked. Batch pending anchor.",
            certificate=CertificatePublicSummary(
                id=cert_record.certificate_id,
                holderName=cert_record.holder_name,
                title=payload_json.get("credential", {}).get("title", ""),
                programme=payload_json.get("credential", {}).get("programme", ""),
                issuedOn=payload_json.get("credential", {}).get("issuedOn", ""),
                institutionName=str(inst_record.name) if inst_record else None,
            ),
            findings=findings,
            durationMs=duration_ms
        )

    findings.append(VerificationFindingItem(
        check="inclusion",
        outcome=FindingOutcome.PASS,
        detail=f"Anchored in batch #{batch_record.batch_id}."
    ))

    duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    return VerificationResult(
        road="A",
        verdict=VerdictCode.VERIFIED_ISSUER_SIGNED,
        summary=f"Signed by {inst_record.name} on {payload_json.get('credential', {}).get('issuedOn', '')}. Not revoked.",
        certificate=CertificatePublicSummary(
            id=cert_record.certificate_id,
            holderName=cert_record.holder_name,
            title=payload_json.get("credential", {}).get("title", ""),
            programme=payload_json.get("credential", {}).get("programme", ""),
            issuedOn=payload_json.get("credential", {}).get("issuedOn", ""),
            institutionName=str(inst_record.name) if inst_record else None,
        ),
        findings=findings,
        anchor={
            "batchId": batch_record.batch_id,
            "kind": batch_record.anchor_kind,
            "receipt": batch_record.anchor_receipt
        },
        durationMs=duration_ms
    )
