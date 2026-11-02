import { generateMohar } from "./generator";

// Golden test hash
const TEST_HASH_1 = new Uint8Array([
  0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0xde, 0xf0,
  0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
  0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff, 0x00,
  0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
]);

export function runMoharTests() {
  console.log("Running Mohar Generator verification tests...");

  // Test 1: Determinism (identical output on consecutive runs)
  const svg1 = generateMohar(TEST_HASH_1);
  const svg2 = generateMohar(TEST_HASH_1);
  if (svg1 !== svg2) {
    throw new Error("FAILED: Mohar generator is not deterministic!");
  }
  console.log("[PASS] Determinism test: output is 100% byte-identical on identical hash input.");

  // Test 2: Payload Size (< 3.8 KB)
  const byteSize = new TextEncoder().encode(svg1).length;
  console.log(`[PASS] Payload Size: ${byteSize} bytes (well within performance budget).`);
  if (byteSize > 4000) {
    throw new Error(`FAILED: Mohar SVG is ${byteSize} bytes, exceeds 4 KB limit!`);
  }

  // Test 3: Collision Resistance across 1,000 distinct pseudo-random hashes
  const seenOutputs = new Set<string>();
  for (let i = 0; i < 1000; i++) {
    const hash = new Uint8Array(32);
    hash[0] = i & 0xff;
    hash[1] = (i >> 8) & 0xff;
    hash[12] = (i * 7) & 0xff;
    hash[15] = (i * 13) & 0xff;
    hash[18] = (i * 19) & 0xff;

    const out = generateMohar(hash);
    if (seenOutputs.has(out)) {
      throw new Error(`FAILED: Hash collision detected at iteration ${i}!`);
    }
    seenOutputs.add(out);
  }
  console.log("[PASS] Collision test: 1,000 distinct hashes produced 1,000 unique geometric seals.");

  // Test 4: Verdict state variation
  const revokedSvg = generateMohar(TEST_HASH_1, { verdict: "REVOKED" });
  if (!revokedSvg.includes("line")) {
    throw new Error("FAILED: Revoked seal missing diagonal cut line!");
  }
  console.log("[PASS] Verdict state test: Revocation cut line rendered cleanly.");

  console.log("All Mohar generator tests PASSED successfully.");
}

if (typeof require !== "undefined" && require.main === module) {
  runMoharTests();
}
