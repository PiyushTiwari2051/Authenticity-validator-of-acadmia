"""Security helpers: Argon2id password hashing, AES-256-GCM envelope encryption,
TOTP multi-factor operations, and token utilities.
"""

import base64
import hashlib
import os
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Any
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import pyotp
import jwt

from backend.app.core.config import settings

# Argon2id according to RFC 9106 / OWASP recommended parameters
# time_cost=3, memory_cost=65536 KiB (64 MB), parallelism=4
ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hash password using Argon2id with memory-hard parameters."""
    return ph.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against Argon2id hash."""
    try:
        return ph.verify(hashed_password, password)
    except (VerifyMismatchError, VerificationError):
        return False


def hash_token(token: str) -> str:
    """Produce SHA-256 hex digest for storage of refresh tokens or API keys."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_ip(ip_address: str, salt: Optional[str] = None) -> str:
    """Hash client IP address with salt to comply with DPDP data minimization."""
    salt_val = salt or settings.JWT_SECRET[:16]
    return hashlib.sha256(f"{salt_val}:{ip_address}".encode("utf-8")).hexdigest()


# AES-256-GCM Envelope Encryption for Key Encryption Keys (KEK)
def _get_aesgcm() -> AESGCM:
    key_bytes = hashlib.sha256(settings.KEK.encode("utf-8")).digest()
    return AESGCM(key_bytes)


def encrypt_secret(plaintext: str) -> str:
    """Encrypt sensitive string (e.g., TOTP secret or private key) using AES-256-GCM."""
    aesgcm = _get_aesgcm()
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    # Pack nonce + ciphertext and base64 encode
    payload = nonce + ciphertext
    return base64.b64encode(payload).decode("utf-8")


def decrypt_secret(encrypted_b64: str) -> str:
    """Decrypt sensitive string using AES-256-GCM."""
    aesgcm = _get_aesgcm()
    payload = base64.b64decode(encrypted_b64.encode("utf-8"))
    nonce = payload[:12]
    ciphertext = payload[12:]
    decrypted = aesgcm.decrypt(nonce, ciphertext, None)
    return decrypted.decode("utf-8")


# TOTP Helpers (RFC 6238)
def generate_totp_secret() -> str:
    """Generate RFC 6238 Base32 TOTP secret."""
    return pyotp.random_base32()


def verify_totp(secret: str, code: str) -> bool:
    """Verify 6-digit TOTP code against secret with 1-step window tolerance."""
    totp = pyotp.TOTP(secret)
    return bool(totp.verify(code, valid_window=1))


def get_totp_uri(secret: str, email: str, issuer: str = "Sanad") -> str:
    """Return otpauth URI for QR code generation."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


# JWT Helpers
def create_access_token(
    user_id: str,
    role: str,
    institution_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    delta = expires_delta or timedelta(minutes=15)
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "inst": institution_id,
        "iat": int(now.timestamp()),
        "exp": int((now + delta).timestamp()),
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate JWT access token."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])


def generate_secure_refresh_token() -> str:
    """Generate high-entropy random refresh token string."""
    return secrets.token_urlsafe(48)
