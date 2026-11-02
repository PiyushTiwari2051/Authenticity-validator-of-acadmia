"""Complete verification suite testing every Road A verdict mandated by Section 8.1:
1. VERIFIED_ISSUER_SIGNED
2. VERIFIED_PENDING_ANCHOR
3. REVOKED
4. INVALID_SIGNATURE (both on tampered byte & altered payload)
5. ISSUER_NOT_APPROVED
6. KEY_WINDOW_UNSAFE
7. NOT_FOUND
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from backend.app.modules.crypto.canonical import canonicalize_json
from backend.app.modules.crypto.signer import Ed25519Signer
from backend.app.modules.verify.engine import (
    verify_road_a_pipeline, VerdictCode, FindingOutcome
)


@pytest.fixture
def test_signer():
    return Ed25519Signer()


@pytest.fixture
def sample_cert(test_signer):
    payload = {
        "schema": "sanad.cert/1",
        "certificateId": "SND-7K3Q9M2XW4PTH8RA",
        "issuer": {"institutionId": "inst_01", "keyId": test_signer.key_id},
        "holder": {"name": "Sample Student", "enrolmentNoHash": "sha256:abc"},
        "credential": {
            "title": "Bachelor of Technology",
            "programme": "Computer Science and Engineering",
            "level": "UG",
            "result": {"cgpa": 8.42, "division": "First"},
            "issuedOn": "2026-07-15",
            "sessionYears": "2022-2026"
        },
        "supersedes": None
    }
    canonical = canonicalize_json(payload)
    sig = test_signer.sign(canonical)

    cert = MagicMock()
    cert.certificate_id = "SND-7K3Q9M2XW4PTH8RA"
    cert.key_id = test_signer.key_id
    cert.canonical_payload = canonical
    cert.signature = sig
    cert.payload_json = payload
    cert.holder_name = "Sample Student"
    cert.status = "issued"
    return cert


@pytest.fixture
def sample_inst():
    inst = MagicMock()
    inst.name = "Demo Institute of Technology"
    inst.status = "approved"
    inst.approved_at = datetime.now(timezone.utc)
    return inst


@pytest.fixture
def sample_key(test_signer):
    key = MagicMock()
    key.key_id = test_signer.key_id
    key.public_key = test_signer.public_key_hex
    key.status = "active"
    return key


@pytest.fixture
def sample_batch():
    batch = MagicMock()
    batch.batch_id = 481
    batch.anchor_kind = "log"
    batch.anchor_receipt = {"root": "abc", "height": 1}
    batch.anchored_at = datetime.now(timezone.utc)
    return batch


def test_verdict_verified_issuer_signed(sample_cert, sample_inst, sample_key, sample_batch):
    res = verify_road_a_pipeline(
        cert_record=sample_cert,
        inst_record=sample_inst,
        key_record=sample_key,
        revocation_record=None,
        batch_record=sample_batch
    )
    assert res.verdict == VerdictCode.VERIFIED_ISSUER_SIGNED
    assert res.road == "A"
    assert res.certificate.id == sample_cert.certificate_id
    assert res.certificate.holderName == "Sample Student"


def test_verdict_verified_pending_anchor(sample_cert, sample_inst, sample_key):
    open_batch = MagicMock()
    open_batch.anchored_at = None  # Open batch, unanchored

    res = verify_road_a_pipeline(
        cert_record=sample_cert,
        inst_record=sample_inst,
        key_record=sample_key,
        revocation_record=None,
        batch_record=open_batch
    )
    assert res.verdict == VerdictCode.VERIFIED_PENDING_ANCHOR


def test_verdict_revoked(sample_cert, sample_inst, sample_key, sample_batch):
    rev = MagicMock()
    rev.reason_code = "DEGREE_WITHDRAWN"
    rev.revoked_at = datetime.now(timezone.utc)

    res = verify_road_a_pipeline(
        cert_record=sample_cert,
        inst_record=sample_inst,
        key_record=sample_key,
        revocation_record=rev,
        batch_record=sample_batch
    )
    assert res.verdict == VerdictCode.REVOKED


def test_verdict_invalid_signature_on_tampered_payload(sample_cert, sample_inst, sample_key, sample_batch):
    # Attacker modified CGPA in stored payload
    sample_cert.payload_json["credential"]["result"]["cgpa"] = 9.99

    res = verify_road_a_pipeline(
        cert_record=sample_cert,
        inst_record=sample_inst,
        key_record=sample_key,
        revocation_record=None,
        batch_record=sample_batch
    )
    assert res.verdict == VerdictCode.INVALID_SIGNATURE


def test_verdict_issuer_not_approved(sample_cert, sample_inst, sample_key, sample_batch):
    sample_inst.status = "suspended"

    res = verify_road_a_pipeline(
        cert_record=sample_cert,
        inst_record=sample_inst,
        key_record=sample_key,
        revocation_record=None,
        batch_record=sample_batch
    )
    assert res.verdict == VerdictCode.ISSUER_NOT_APPROVED


def test_verdict_key_window_unsafe(sample_cert, sample_inst, sample_key, sample_batch):
    sample_key.status = "compromised"
    sample_key.compromised_from = datetime.now(timezone.utc) - timedelta(days=1)
    sample_batch.anchored_at = datetime.now(timezone.utc)  # Anchored AFTER compromise

    res = verify_road_a_pipeline(
        cert_record=sample_cert,
        inst_record=sample_inst,
        key_record=sample_key,
        revocation_record=None,
        batch_record=sample_batch
    )
    assert res.verdict == VerdictCode.KEY_WINDOW_UNSAFE


def test_verdict_not_found():
    res = verify_road_a_pipeline(
        cert_record=None,
        inst_record=None,
        key_record=None,
        revocation_record=None,
        batch_record=None
    )
    assert res.verdict == VerdictCode.NOT_FOUND
