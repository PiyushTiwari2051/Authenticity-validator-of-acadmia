"""RFC 8785 JSON Canonicalization Scheme (JCS) implementation.
Ensures deterministic, platform-independent byte sequences for cryptographic signing.
"""

import json
from typing import Any
import canonicaljson


def canonicalize_json(data: Any) -> bytes:
    """Canonicalize a Python dictionary or JSON-serializable structure according to RFC 8785.
    Output is UTF-8 encoded bytes with sorted keys, no extraneous whitespace,
    and standardized number/character representations.
    """
    # canonicaljson provides RFC 8785 compliant canonical byte serialization
    return canonicaljson.encode_canonical_json(data)


def canonicalize_to_str(data: Any) -> str:
    """Return canonical JSON as a UTF-8 string."""
    return canonicalize_json(data).decode("utf-8")
