"""Standalone offline CLI tool for jury verification of Merkle inclusion proofs.
Zero network access, zero server dependencies.
Usage:
    python tools/verify_inclusion.py --leaf <leaf_hex> --root <root_hex> --proof-json <proof_json_file_or_string>
"""

import argparse
import hashlib
import json
import sys


def hash_node(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(b"\x01" + left + right).digest()


def verify_proof(leaf_hex: str, root_hex: str, proof_steps: list[dict[str, str]]) -> bool:
    current = bytes.fromhex(leaf_hex)
    for step in proof_steps:
        sibling = bytes.fromhex(step["hash"])
        if step["direction"] == "left":
            current = hash_node(sibling, current)
        else:
            current = hash_node(current, sibling)
    return current.hex().lower() == root_hex.lower()


def main():
    parser = argparse.ArgumentParser(description="Sanad Merkle Inclusion Proof Standalone Verifier")
    parser.add_argument("--leaf", required=True, help="Leaf hash in hex")
    parser.add_argument("--root", required=True, help="Expected Merkle batch root in hex")
    parser.add_argument("--proof", required=True, help="Proof steps as JSON string or path to JSON file")

    args = parser.parse_args()

    try:
        if args.proof.startswith("[") or args.proof.startswith("{"):
            steps = json.loads(args.proof)
        else:
            with open(args.proof, "r") as f:
                steps = json.load(f)
    except Exception as e:
        print(f"Error parsing proof JSON: {e}", file=sys.stderr)
        sys.exit(1)

    is_valid = verify_proof(args.leaf, args.root, steps)
    if is_valid:
        print("\n[SUCCESS] The leaf hash is mathematically proven to be included in Merkle root.")
        print(f"Root: {args.root}")
        print(f"Leaf: {args.leaf}")
        sys.exit(0)
    else:
        print("\n[FAILED] Inclusion proof verification failed! Leaf is NOT in the specified batch root.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
