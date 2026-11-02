/**
 * Mohar (मुहर) Generator - Pure mathematical guilloche rosette generator.
 * Inputs: 32 raw hash bytes (SHA-256 Merkle leaf hash).
 * Outputs: Clean, deterministic, accessible SVG string (< 3.5 KB) with 0 randomness, 0 clock.
 */

export interface MoharOptions {
  size?: number;
  inkColor?: string;
  accentColor?: string;
  monogram?: string;
  verdict?:
    | "VERIFIED_ISSUER_SIGNED"
    | "VERIFIED_PENDING_ANCHOR"
    | "REVOKED"
    | "INVALID_SIGNATURE"
    | "NOT_FOUND"
    | "CONSISTENT_WITH_REGISTRY"
    | "NEEDS_REVIEW"
    | "LIKELY_ALTERED"
    | "CANNOT_VERIFY";
}

const COPRIME_LOBES = [5, 7, 8, 9, 11, 13, 15, 17];

export function generateMohar(hashBytes: Uint8Array, options: MoharOptions = {}): string {
  const size = options.size || 280;
  const ink = options.inkColor || "currentColor";
  const accent = options.accentColor || "#C2412D";
  const monogram = options.monogram || "SD";
  const verdict = options.verdict || "VERIFIED_ISSUER_SIGNED";

  const cx = 140;
  const cy = 140;

  // 1. Not Found / Cannot Verify: Empty or pale ring
  if (verdict === "NOT_FOUND") {
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 280" width="${size}" height="${size}" role="img" aria-label="Empty Seal - Not Found">
      <circle cx="${cx}" cy="${cy}" r="130" fill="none" stroke="${ink}" stroke-width="1.5" stroke-dasharray="4 6" opacity="0.4" />
      <text x="${cx}" y="${cy + 5}" font-family="Fraunces, serif" font-size="14" fill="${ink}" opacity="0.5" text-anchor="middle">NOT FOUND</text>
    </svg>`;
  }

  // 2. Ring Code: 96 ticks around outer circumference (bytes 0 to 11)
  const ringTicks: string[] = [];
  const rOuter = 136;
  for (let i = 0; i < 96; i++) {
    const byteIdx = Math.floor(i / 8);
    const bitIdx = 7 - (i % 8);
    const isBitSet = ((hashBytes[byteIdx] >> bitIdx) & 1) === 1;
    const tickLen = isBitSet ? 7 : 3.5;
    const angle = (2 * Math.PI * i) / 96;

    const x1 = (cx + (rOuter - tickLen) * Math.cos(angle)).toFixed(2);
    const y1 = (cy + (rOuter - tickLen) * Math.sin(angle)).toFixed(2);
    const x2 = (cx + rOuter * Math.cos(angle)).toFixed(2);
    const y2 = (cy + rOuter * Math.sin(angle)).toFixed(2);

    ringTicks.push(`M${x1},${y1}L${x2},${y2}`);
  }

  // 3. Three Concentric Hypotrochoids (bytes 12 to 20)
  // Parametric: x = (R-r)*cos(t) + d*cos((R-r)/r * t)
  const layers = [
    { R: 118, byteLobe: hashBytes[12], byteD: hashBytes[15], byteRot: hashBytes[18] },
    { R: 92, byteLobe: hashBytes[13], byteD: hashBytes[16], byteRot: hashBytes[19] },
    { R: 68, byteLobe: hashBytes[14], byteD: hashBytes[17], byteRot: hashBytes[20] },
  ];

  const rosettePaths: string[] = [];
  const isAdvisory = verdict.startsWith("CONSISTENT") || verdict.startsWith("NEEDS") || verdict.startsWith("LIKELY");

  layers.forEach((layer, lIdx) => {
    const lobes = COPRIME_LOBES[layer.byteLobe % COPRIME_LOBES.length];
    const r = (layer.R * (lobes - 1)) / lobes;
    const dMin = 0.45 * r;
    const dMax = 0.9 * r;
    const d = dMin + ((dMax - dMin) * layer.byteD) / 255;
    let rot = (2 * Math.PI * layer.byteRot) / 255;

    // Invalid signature effect: layers drift out of register
    if (verdict === "INVALID_SIGNATURE" && lIdx === 2) {
      rot += 0.8;
    }

    const steps = 180;
    const points: string[] = [];
    for (let s = 0; s <= steps; s++) {
      const t = (2 * Math.PI * s) / steps;
      const angleArg = ((layer.R - r) / r) * t + rot;
      const x = (cx + (layer.R - r) * Math.cos(t + rot) + d * Math.cos(angleArg)).toFixed(2);
      const y = (cy + (layer.R - r) * Math.sin(t + rot) - d * Math.sin(angleArg)).toFixed(2);
      points.push(s === 0 ? `M${x},${y}` : `L${x},${y}`);
    }
    points.push("Z");
    rosettePaths.push(points.join(""));
  });

  // 4. Accent Pressed Notch at top for VERIFIED_ISSUER_SIGNED
  const showNotch = verdict === "VERIFIED_ISSUER_SIGNED";
  const notchArc = showNotch
    ? `<path d="M132,4 A136,136 0 0,1 148,4" fill="none" stroke="${accent}" stroke-width="4" stroke-linecap="round" />`
    : "";

  // 5. Diagonal cut if REVOKED
  const cutLine =
    verdict === "REVOKED"
      ? `<line x1="30" y1="250" x2="250" y2="30" stroke="${accent}" stroke-width="3" stroke-linecap="round" />`
      : "";

  // Center medallion text
  const centerText = isAdvisory ? "ADVISORY" : monogram;
  const centerFontSize = isAdvisory ? "9" : "15";

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 280" width="${size}" height="${size}" role="img" aria-label="Mohar Seal ${verdict}">
    <g class="mohar-root" stroke="${ink}">
      <!-- Outer Ring Code -->
      <path d="${ringTicks.join("")}" fill="none" stroke-width="1" opacity="${verdict === "REVOKED" ? "0.35" : "0.75"}" />
      
      <!-- Concentric Rosette Paths -->
      ${rosettePaths
        .map(
          (p) =>
            `<path d="${p}" fill="none" stroke-width="0.75" stroke-dasharray="${isAdvisory ? "2 3" : "none"}" opacity="${
              verdict === "INVALID_SIGNATURE" ? "0.4" : "0.8"
            }" />`
        )
        .join("\n      ")}
      
      <!-- Top Accent Notch -->
      ${notchArc}

      <!-- Center Medallion Knockout -->
      <circle cx="${cx}" cy="${cy}" r="26" fill="var(--bg-surface, #FAF6EC)" stroke="${ink}" stroke-width="1.2" />
      <text x="${cx}" y="${cy + 5}" font-family="Fraunces, Georgia, serif" font-size="${centerFontSize}" font-weight="bold" letter-spacing="1" fill="${ink}" text-anchor="middle">
        ${centerText}
      </text>

      <!-- Revocation Cut -->
      ${cutLine}
    </g>
  </svg>`;
}
