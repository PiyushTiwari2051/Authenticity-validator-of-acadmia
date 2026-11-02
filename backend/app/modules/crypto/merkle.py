"""RFC 6962 Domain-Separated Merkle Tree & Inclusion Proof Generator.
- Leaf hashing: SHA-256(0x00 || bytes)
- Node hashing: SHA-256(0x01 || left || right)
Blocks second-preimage attacks and allows independent inclusion proof verification.
"""

import hashlib
from typing import Optional


def hash_leaf(data: bytes) -> bytes:
    """Hash leaf with RFC 6962 0x00 domain separator prefix."""
    return hashlib.sha256(b"\x00" + data).digest()


def hash_node(left: bytes, right: bytes) -> bytes:
    """Hash interior node with RFC 6962 0x01 domain separator prefix."""
    return hashlib.sha256(b"\x01" + left + right).digest()


class MerkleTree:
    """Deterministic Binary Merkle Tree with inclusion proof construction."""

    def __init__(self, leaf_hashes: list[bytes]):
        if not leaf_hashes:
            raise ValueError("Cannot construct a Merkle tree with zero leaves.")
        self.leaves: list[bytes] = list(leaf_hashes)
        self.levels: list[list[bytes]] = [self.leaves]
        self._build_tree()

    def _build_tree(self) -> None:
        current = self.leaves
        while len(current) > 1:
            next_level: list[bytes] = []
            for i in range(0, len(current), 2):
                left = current[i]
                if i + 1 < len(current):
                    right = current[i + 1]
                else:
                    # Duplicate last node if odd number of leaves (RFC 6962 approach)
                    right = left
                next_level.append(hash_node(left, right))
            self.levels.append(next_level)
            current = next_level

    @property
    def root(self) -> bytes:
        return self.levels[-1][0]

    @property
    def root_hex(self) -> str:
        return self.root.hex()

    def get_inclusion_proof(self, leaf_index: int) -> list[dict[str, str]]:
        """Compute the sibling audit path (inclusion proof) for a given leaf index.
        Returns a list of dicts: [{'direction': 'left'|'right', 'hash': hex_string}].
        """
        if leaf_index < 0 or leaf_index >= len(self.leaves):
            raise IndexError("Leaf index out of bounds.")

        proof: list[dict[str, str]] = []
        idx = leaf_index

        for level in self.levels[:-1]:
            is_right_child = (idx % 2 == 1)
            sibling_idx = idx - 1 if is_right_child else idx + 1

            if sibling_idx >= len(level):
                # Odd node was duplicated
                sibling_hash = level[idx]
            else:
                sibling_hash = level[sibling_idx]

            proof.append({
                "direction": "left" if is_right_child else "right",
                "hash": sibling_hash.hex()
            })
            idx //= 2

        return proof


def verify_merkle_proof(leaf_hash: bytes, proof: list[dict[str, str]], expected_root_hex: str) -> bool:
    """Verify an inclusion proof independently without database or server state."""
    current = leaf_hash
    for step in proof:
        sibling = bytes.fromhex(step["hash"])
        if step["direction"] == "left":
            current = hash_node(sibling, current)
        else:
            current = hash_node(current, sibling)
    return current.hex().lower() == expected_root_hex.lower()
