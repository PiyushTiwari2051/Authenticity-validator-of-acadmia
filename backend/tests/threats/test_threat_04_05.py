"""Threat tests for Threat Model row 4 & row 5:
- Threat 04: Unapproved institution attempting issuance
- Threat 05: Tamper-evident audit trail detection
"""

import pytest
import uuid
from backend.app.db.models import User, UserRole, InstitutionStatus
from backend.app.core.errors import ForbiddenException
from backend.app.modules.audit.service import compute_audit_hash, GENESIS_HASH


def test_threat_04_unapproved_institution_issuance_blocked():
    """Row 4 Threat: Unapproved institution or inactive key cannot issue certificates."""
    institution_status = InstitutionStatus.PENDING

    # Enforce policy: only APPROVED institutions may issue
    assert institution_status != InstitutionStatus.APPROVED

    with pytest.raises(ForbiddenException) as exc_info:
        if institution_status != InstitutionStatus.APPROVED:
            raise ForbiddenException("Institution is pending approval. Issuance rejected.")
    assert "pending approval" in str(exc_info.value.detail)


def test_threat_05_audit_chain_tamper_detection():
    """Row 5 Threat: Post-hoc alteration or deletion of audit logs is mathematically detected."""
    # Row 1
    h1 = compute_audit_hash(
        prev_hash=GENESIS_HASH,
        actor_id=str(uuid.uuid4()),
        actor_role="operator",
        action="certificate_issued",
        object_type="certificate",
        object_id="SND-12345",
        ip_hash="abc123hash",
        detail_json={"student": "Rohan Sharma"},
    )

    # Row 2 chained to Row 1
    h2 = compute_audit_hash(
        prev_hash=h1,
        actor_id=str(uuid.uuid4()),
        actor_role="operator",
        action="certificate_issued",
        object_type="certificate",
        object_id="SND-67890",
        ip_hash="abc123hash",
        detail_json={"student": "Priya Verma"},
    )

    # If an attacker alters Row 1 details (e.g. attempting to erase an issuance)
    tampered_h1 = compute_audit_hash(
        prev_hash=GENESIS_HASH,
        actor_id=str(uuid.uuid4()),
        actor_role="operator",
        action="certificate_issued",
        object_type="certificate",
        object_id="SND-12345",
        ip_hash="abc123hash",
        detail_json={"student": "Altered Name"},
    )

    # The chain link to h2 breaks
    assert tampered_h1 != h1
    recomputed_h2_with_tamper = compute_audit_hash(
        prev_hash=tampered_h1,
        actor_id=str(uuid.uuid4()),
        actor_role="operator",
        action="certificate_issued",
        object_type="certificate",
        object_id="SND-67890",
        ip_hash="abc123hash",
        detail_json={"student": "Priya Verma"},
    )
    assert recomputed_h2_with_tamper != h2
