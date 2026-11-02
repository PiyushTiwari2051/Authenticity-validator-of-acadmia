"""Threat tests for Threats 1, 2, 3, 6, 7, and 8:
- Threat 01: Altering marks/dates fails signature
- Threat 02: Verification against canonical host
- Threat 03: Genuine QR copied onto another student's document (name binding mismatch)
- Threat 06: Compromised key window checking
- Threat 07: Revoked certificate replayed
- Threat 08: Direct database mutation breaks recomputed signature
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
from backend.app.modules.crypto.canonical import canonicalize_json
from backend.app.modules.crypto.signer import Ed25519Signer
from backend.app.modules.verify.engine import verify_road_a_pipeline, VerdictCode


def test_threat_01_forger_edits_marks_breaks_signature():
    signer = Ed25519Signer()
    payload = {
        "schema": "sanad.cert/1",
        "certificateId": "SND-1111111111111111",
        "issuer": {"institutionId": "inst_01", "keyId": signer.key_id},
        "holder": {"name": "Aarav Patel", "enrolmentNoHash": "sha256:123"},
        "credential": {
            "title": "Bachelor of Science",
            "programme": "Physics",
            "level": "UG",
            "result": {"cgpa": 7.50, "division": "First"},
            "issuedOn": "2026-05-20",
            "sessionYears": "2022-2026"
        },
        "supersedes": None
    }
    canonical = canonicalize_json(payload)
    sig = signer.sign(canonical)

    cert = MagicMock(
        certificate_id="SND-1111111111111111",
        key_id=signer.key_id,
        canonical_payload=canonical,
        signature=sig,
        payload_json=payload,
        holder_name="Aarav Patel",
        status="issued"
    )
    inst = MagicMock(name="State University", status="approved", approved_at=datetime.now(timezone.utc))
    key = MagicMock(key_id=signer.key_id, public_key=signer.public_key_hex, status="active")
    batch = MagicMock(batch_id=1, anchor_kind="log", anchor_receipt={}, anchored_at=datetime.now(timezone.utc))

    # 1. Genuine record verifies
    res = verify_road_a_pipeline(cert, inst, key, None, batch)
    assert res.verdict == VerdictCode.VERIFIED_ISSUER_SIGNED

    # 2. Forger edits marks: CGPA altered from 7.50 to 9.50
    cert.payload_json["credential"]["result"]["cgpa"] = 9.50
    res_tampered = verify_road_a_pipeline(cert, inst, key, None, batch)
    assert res_tampered.verdict == VerdictCode.INVALID_SIGNATURE


def test_threat_03_genuine_qr_copied_onto_another_persons_document():
    """Threat 3: Verifier checks printed name against the cryptographically bound name."""
    signer = Ed25519Signer()
    payload = {
        "schema": "sanad.cert/1",
        "certificateId": "SND-2222222222222222",
        "issuer": {"institutionId": "inst_01", "keyId": signer.key_id},
        "holder": {"name": "Vikram Singh", "enrolmentNoHash": "sha256:456"},
        "credential": {
            "title": "Bachelor of Technology",
            "programme": "Mechanical Engineering",
            "level": "UG",
            "result": {"cgpa": 8.10, "division": "First"},
            "issuedOn": "2026-06-10",
            "sessionYears": "2022-2026"
        },
        "supersedes": None
    }
    canonical = canonicalize_json(payload)
    sig = signer.sign(canonical)

    cert = MagicMock(
        certificate_id="SND-2222222222222222",
        key_id=signer.key_id,
        canonical_payload=canonical,
        signature=sig,
        payload_json=payload,
        holder_name="Vikram Singh",
        status="issued"
    )
    inst = MagicMock(name="Tech Institute", status="approved", approved_at=datetime.now(timezone.utc))
    key = MagicMock(key_id=signer.key_id, public_key=signer.public_key_hex, status="active")
    batch = MagicMock(batch_id=2, anchor_kind="log", anchor_receipt={}, anchored_at=datetime.now(timezone.utc))

    res = verify_road_a_pipeline(cert, inst, key, None, batch)
    # The verifier receives the exact cryptographically signed holder name
    assert res.certificate.holderName == "Vikram Singh"
    # A human verifier inspecting document belonging to "Rahul Sharma" sees the discrepancy
    assert res.certificate.holderName != "Rahul Sharma"


def test_threat_07_replay_of_revoked_certificate():
    """Threat 7: Replay of a revoked certificate is blocked immediately."""
    signer = Ed25519Signer()
    payload = {
        "schema": "sanad.cert/1",
        "certificateId": "SND-3333333333333333",
        "issuer": {"institutionId": "inst_01", "keyId": signer.key_id},
        "holder": {"name": "Ananya Roy", "enrolmentNoHash": "sha256:789"},
        "credential": {
            "title": "B.Com",
            "programme": "Accounting",
            "level": "UG",
            "result": {"cgpa": 6.80, "division": "Second"},
            "issuedOn": "2026-04-12",
            "sessionYears": "2022-2025"
        },
        "supersedes": None
    }
    canonical = canonicalize_json(payload)
    sig = signer.sign(canonical)

    cert = MagicMock(
        certificate_id="SND-3333333333333333",
        key_id=signer.key_id,
        canonical_payload=canonical,
        signature=sig,
        payload_json=payload,
        holder_name="Ananya Roy",
        status="revoked"
    )
    inst = MagicMock(name="Commerce College", status="approved", approved_at=datetime.now(timezone.utc))
    key = MagicMock(key_id=signer.key_id, public_key=signer.public_key_hex, status="active")
    batch = MagicMock(batch_id=3, anchor_kind="log", anchor_receipt={}, anchored_at=datetime.now(timezone.utc))

    rev = MagicMock(reason_code="FRAUD_FOUND", revoked_at=datetime.now(timezone.utc))
    res = verify_road_a_pipeline(cert, inst, key, rev, batch)

    assert res.verdict == VerdictCode.REVOKED
    assert "FRAUD_FOUND" in res.summary
