"""Signer Interface and ServerSigner implementation.
Signs RFC 8785 canonical bytes using Ed25519 with domain-separation prefix.
"""

from abc import ABC, abstractmethod
import base64
import hashlib
from typing import Optional
import nacl.signing
import nacl.encoding

# Fixed static domain separation string mandated by Section 6.2
DOMAIN_PREFIX = b"SANAD-CERT-v1\n"


def compute_key_id(public_key_bytes: bytes) -> str:
    """Derive keyId: first 8 bytes of SHA-256 of the public key, hex encoded (16 chars)."""
    digest = hashlib.sha256(public_key_bytes).digest()
    return digest[:8].hex()


class Signer(ABC):
    """Abstract Signer interface separating signing mechanics from key storage."""

    @abstractmethod
    def sign(self, canonical_bytes: bytes) -> str:
        """Sign canonical bytes prefixed with DOMAIN_PREFIX. Returns hex signature string."""
        pass

    @property
    @abstractmethod
    def key_id(self) -> str:
        """Return the 16-character hex key identifier."""
        pass

    @property
    @abstractmethod
    def public_key_hex(self) -> str:
        """Return the hex-encoded Ed25519 public key."""
        pass


class Ed25519Signer(Signer):
    """Direct in-memory / Server-held Ed25519 Signer."""

    def __init__(self, private_key_bytes: Optional[bytes] = None):
        if private_key_bytes is None:
            self._signing_key = nacl.signing.SigningKey.generate()
        else:
            self._signing_key = nacl.signing.SigningKey(private_key_bytes)
        self._verify_key = self._signing_key.verify_key
        self._key_id = compute_key_id(self._verify_key.encode())

    @property
    def key_id(self) -> str:
        return self._key_id

    @property
    def public_key_hex(self) -> str:
        return self._verify_key.encode(encoder=nacl.encoding.HexEncoder).decode("utf-8")

    @property
    def private_key_bytes(self) -> bytes:
        return self._signing_key.encode()

    def sign(self, canonical_bytes: bytes) -> str:
        """Prefix with domain string and produce 64-byte Ed25519 signature."""
        msg = DOMAIN_PREFIX + canonical_bytes
        signed = self._signing_key.sign(msg)
        return signed.signature.hex()


def verify_signature(public_key_hex: str, canonical_bytes: bytes, signature_hex: str) -> bool:
    """Verify Ed25519 signature over DOMAIN_PREFIX + canonical_bytes."""
    try:
        verify_key = nacl.signing.VerifyKey(public_key_hex, encoder=nacl.encoding.HexEncoder)
        msg = DOMAIN_PREFIX + canonical_bytes
        sig_bytes = bytes.fromhex(signature_hex)
        verify_key.verify(msg, sig_bytes)
        return True
    except Exception:
        return False
