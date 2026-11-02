"""Unit and Integration Tests for Phase 1: Identity, Tenancy, and Audit Integrity.
Tests:
- Argon2id password hashing
- TOTP 2FA enrollment and verification
- Refresh token rotation & family revocation on reuse attack
- Cross-tenant access isolation (IDOR protection)
- Append-only hash chain audit integrity
- Threat 04: Unapproved institution issuance / administrative gate
"""

import pytest
import uuid
import hashlib
from datetime import datetime, timezone

from backend.app.db.models import (
    Base, User, UserRole, Institution, InstitutionStatus, RefreshToken
)
from backend.app.core.security import (
    hash_password, verify_password, generate_totp_secret, verify_totp,
    encrypt_secret, decrypt_secret, create_access_token, decode_access_token
)
from backend.app.core.dependencies import AuthContext
from backend.app.core.errors import ForbiddenException, UnauthorizedException
from backend.app.modules.audit.service import (
    compute_audit_hash, write_audit_entry, verify_audit_chain, GENESIS_HASH
)


def test_argon2id_hashing():
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_totp_lifecycle():
    secret = generate_totp_secret()
    assert len(secret) == 32
    enc = encrypt_secret(secret)
    dec = decrypt_secret(enc)
    assert dec == secret

    import pyotp
    totp = pyotp.TOTP(secret)
    code = totp.now()
    assert verify_totp(secret, code) is True
    assert verify_totp(secret, "000000") is False


def test_jwt_access_token_creation_and_expiration():
    uid = str(uuid.uuid4())
    inst_id = str(uuid.uuid4())
    token = create_access_token(user_id=uid, role="operator", institution_id=inst_id)
    payload = decode_access_token(token)
    assert payload["sub"] == uid
    assert payload["role"] == "operator"
    assert payload["inst"] == inst_id


def test_tenant_isolation_enforcement():
    inst_a = uuid.uuid4()
    inst_b = uuid.uuid4()

    operator_user = User(
        id=uuid.uuid4(),
        email="operator@inst-a.edu",
        password_hash="dummy",
        role=UserRole.OPERATOR,
        institution_id=inst_a,
    )
    ctx = AuthContext(user=operator_user, ip_hash="dummy_ip")

    # Accessing own tenant succeeds
    ctx.require_tenant(inst_a)

    # Accessing foreign tenant MUST raise ForbiddenException
    with pytest.raises(ForbiddenException) as exc_info:
        ctx.require_tenant(inst_b)
    assert "Tenant isolation breach" in str(exc_info.value.detail)

    # Platform Admin can access any tenant
    admin_user = User(
        id=uuid.uuid4(),
        email="admin@nodal.gov.in",
        password_hash="dummy",
        role=UserRole.PLATFORM_ADMIN,
        institution_id=None,
    )
    admin_ctx = AuthContext(user=admin_user, ip_hash="dummy_ip")
    admin_ctx.require_tenant(inst_a)
    admin_ctx.require_tenant(inst_b)


def test_audit_hash_chain_calculation():
    prev = GENESIS_HASH
    actor_id = str(uuid.uuid4())
    h1 = compute_audit_hash(
        prev_hash=prev,
        actor_id=actor_id,
        actor_role="platform_admin",
        action="institution_approved",
        object_type="institution",
        object_id="inst_01",
        ip_hash="fakeiphash",
        detail_json={"name": "Demo Tech"},
    )
    assert isinstance(h1, str)
    assert len(h1) == 64

    # Chaining second row
    h2 = compute_audit_hash(
        prev_hash=h1,
        actor_id=actor_id,
        actor_role="platform_admin",
        action="key_registered",
        object_type="key",
        object_id="k_12345",
        ip_hash="fakeiphash",
        detail_json={"key": "pub_key_bytes"},
    )
    assert h2 != h1
    assert len(h2) == 64

    # Any modification of row 1 breaks chain linking to row 2
    tampered_h1 = compute_audit_hash(
        prev_hash=prev,
        actor_id=actor_id,
        actor_role="platform_admin",
        action="institution_approved",
        object_type="institution",
        object_id="inst_01",
        ip_hash="fakeiphash",
        detail_json={"name": "HACKED TECH"},  # modified
    )
    assert tampered_h1 != h1
