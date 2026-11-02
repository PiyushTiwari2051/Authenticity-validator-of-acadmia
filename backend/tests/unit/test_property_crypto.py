"""Property-based tests for RFC 8785 Canonical JSON & Merkle Tree proofs.
Validates:
- Canonicalization determinism across any key ordering.
- Merkle proofs verify for arbitrary random leaves, and any tampered byte fails.
"""

from hypothesis import given, strategies as st
import hashlib
import json
from backend.app.modules.crypto.canonical import canonicalize_json
from backend.app.modules.crypto.merkle import MerkleTree, verify_merkle_proof, hash_leaf


@given(st.dictionaries(keys=st.text(min_size=1, max_size=10), values=st.integers(), min_size=1, max_size=10))
def test_canonical_json_key_order_invariance(d):
    """Property: Canonical bytes must be 100% identical regardless of dictionary key insertion order."""
    keys = list(d.keys())
    reversed_d = {k: d[k] for k in reversed(keys)}

    b1 = canonicalize_json(d)
    b2 = canonicalize_json(reversed_d)
    assert b1 == b2


@given(st.lists(st.binary(min_size=1, max_size=64), min_size=1, max_size=20))
def test_merkle_tree_inclusion_proof_property(raw_items):
    """Property: For any arbitrary Merkle tree, every leaf's inclusion proof verifies,
    and altering any single byte in a leaf causes verification to fail.
    """
    leaf_hashes = [hash_leaf(item) for item in raw_items]
    tree = MerkleTree(leaf_hashes)
    root_hex = tree.root_hex

    for idx, leaf_hash in enumerate(leaf_hashes):
        proof = tree.get_inclusion_proof(idx)
        # Original leaf verifies
        assert verify_merkle_proof(leaf_hash, proof, root_hex) is True

        # Tampered leaf fails
        tampered_leaf = hash_leaf(raw_items[idx] + b"_tampered")
        assert verify_merkle_proof(tampered_leaf, proof, root_hex) is False
