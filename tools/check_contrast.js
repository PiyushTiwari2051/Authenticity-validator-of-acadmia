const fs = require('fs');

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  return [r, g, b].map(c => c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
}

function getLuminance(hex) {
  const [r, g, b] = hexToRgb(hex);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function getContrast(hex1, hex2) {
  const l1 = getLuminance(hex1);
  const l2 = getLuminance(hex2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

const tokens = JSON.parse(fs.readFileSync('frontend/design-tokens/tokens.json', 'utf8'));
const light = tokens.color.light;
const bgLight = light['paper-50'];

console.log('=== WCAG 2.2 AA Contrast Verification (Light: paper-50 #FAF6EC) ===');
const pairs = [
  ['ink-900 (Main text)', light['ink-900'], 4.5],
  ['ink-700 (Secondary)', light['ink-700'], 4.5],
  ['ink-500 (Captions)', light['ink-500'], 4.5],
  ['neel (Links/Buttons)', light['neel'], 4.5],
  ['verified (Passed badge)', light['verified'], 4.5],
  ['danger (Revoked/Error)', light['danger'], 4.5],
  ['caution (Warning text)', light['caution'], 4.5]
];

let allPass = true;
for (const [name, color, target] of pairs) {
  const ratio = parseFloat(getContrast(bgLight, color).toFixed(2));
  const pass = ratio >= target;
  if (!pass) allPass = false;
  console.log(`[${pass ? 'PASS' : 'FAIL'}] ${name} (${color}): ${ratio}:1 (Target >= ${target}:1)`);
}

if (allPass) {
  console.log('\nAll light palette text contrast ratios satisfy WCAG 2.2 AA criteria (>= 4.5:1).');
} else {
  console.error('\nContrast failure detected! Adjust token colors.');
  process.exit(1);
}
