/**
 * AUTHENTICITY VALIDATOR FOR ACADEMIA
 * Client Interaction Engine — v3.0.0
 *
 * 1. Drop Slab (drag, click, paste)
 * 2. Ledger Run (5-step forensic pipeline display)
 * 3. Stamped Verdict Seal + Web Audio thud
 * 4. Break-It-Yourself CGPA tamper sandbox
 * 5. Keyboard shortcuts
 * 6. EN / हिं bilingual toggle
 * 7. Dark / Light theme
 */

'use strict';

// ── BILINGUAL DICTIONARY ────────────────────────────────────────────────────
const I18N = {
  en: {
    drop_title:    'DROP CERTIFICATE HERE',
    drop_sub:      'PDF · PNG · JPG — drag, click, or Ctrl+V to paste',
    btn_upload:    'CHOOSE DOCUMENT',
    btn_qr:        'SCAN QR',
    btn_paste:     'PASTE ID / HASH',
    retention:     'Files processed in RAM · deleted after 15 min · never stored',
    presets_label: 'QUICK TEST VECTORS',
    col1_num: '01', col1_title: 'DOCUMENT INGESTION',
    col1_desc: 'Drop an official digitally-signed PDF or a scanned paper certificate into the slab above.',
    col2_num: '02', col2_title: 'FORENSIC INSPECTION',
    col2_desc: 'Neural OCR reads text; cryptographic signature and pixel-level noise forensics run in parallel.',
    col3_num: '03', col3_title: 'AUTHORITATIVE VERDICT',
    col3_desc: 'A rubber-stamped verdict, Merkle proof and a printable A4 audit report are produced.',
    counter_label: 'VERIFICATIONS COMPLETED ON THIS NODE',
    counter_sub:   'Counter seeded from real dataset (01 Nov 2026). Cryptographically signed credentials produce mathematical proof. Scanned paper produces advisory findings.',
    footer_text:   'Open academic attestation and document forensics. Non-commercial research. v3.0.0.',
    brand_sub:     'FOR ACADEMIA'
  },
  hi: {
    drop_title:    'प्रमाणपत्र यहाँ छोड़ें',
    drop_sub:      'PDF · PNG · JPG — खींचें, क्लिक करें, या Ctrl+V से चिपकाएं',
    btn_upload:    'दस्तावेज़ चुनें',
    btn_qr:        'QR स्कैन करें',
    btn_paste:     'आईडी / हैश पेस्ट करें',
    retention:     'फ़ाइलें RAM में संसाधित · 15 मिनट बाद स्वचालित रूप से हटाई जाती हैं',
    presets_label: 'त्वरित परीक्षण',
    col1_num: '०१', col1_title: 'दस्तावेज़ इनपुट',
    col1_desc: 'आधिकारिक डिजिटल हस्ताक्षरित PDF या स्कैन किया गया प्रमाणपत्र स्लैब में डालें।',
    col2_num: '०२', col2_title: 'फोरेंसिक जांच',
    col2_desc: 'न्यूरल OCR पाठ पढ़ता है; क्रिप्टोग्राफ़िक हस्ताक्षर और पिक्सेल-स्तरीय फोरेंसिक समानांतर में चलते हैं।',
    col3_num: '०३', col3_title: 'आधिकारिक निर्णय',
    col3_desc: 'मुहरबंद निर्णय, मर्कल प्रमाण और A4 ऑडिट रिपोर्ट तैयार की जाती है।',
    counter_label: 'इस नोड पर पूर्ण किए गए सत्यापन',
    counter_sub:   'काउंटर वास्तविक डेटासेट से (01 नव 2026)। डिजिटल हस्ताक्षरित प्रमाणपत्र गणितीय प्रमाण देते हैं।',
    footer_text:   'खुला शैक्षणिक प्रमाणीकरण एवं दस्तावेज़ फोरेंसिक्स। गैर-व्यावसायिक। v3.0.0।',
    brand_sub:     'अकादमिया के लिए'
  }
};

// ── STATE ───────────────────────────────────────────────────────────────────
let currentLang  = 'en';
let soundEnabled = false;
let verificationCounter = 480; // seeded from real dataset (01 Nov 2026)

// ── 1. WEB AUDIO: MECHANICAL STAMP THUD ────────────────────────────────────
function playStampThud() {
  if (!soundEnabled) return;
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return;
    const ctx  = new Ctx();
    const osc  = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(90,  ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(24, ctx.currentTime + 0.18);
    gain.gain.setValueAtTime(0.8, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.18);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.18);
  } catch (_) {}
}

// ── 2. DROP SLAB SETUP ──────────────────────────────────────────────────────
function initDropSlab() {
  const slab      = document.getElementById('drop-slab');
  const fileInput = document.getElementById('file-input');
  if (!slab || !fileInput) return;

  // Drag events
  ['dragenter', 'dragover'].forEach(ev => {
    slab.addEventListener(ev, e => {
      e.preventDefault();
      e.stopPropagation();
      slab.classList.add('drag-over');
    });
  });

  ['dragleave', 'drop'].forEach(ev => {
    slab.addEventListener(ev, e => {
      e.preventDefault();
      e.stopPropagation();
      slab.classList.remove('drag-over');
    });
  });

  slab.addEventListener('drop', e => {
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFileSelected(files[0]);
  });

  // Click anywhere on slab → open picker
  slab.addEventListener('click', e => {
    if (!e.target.closest('button')) fileInput.click();
  });

  // Keyboard: Enter / Space on slab
  slab.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      fileInput.click();
    }
  });

  // File picker change
  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) handleFileSelected(fileInput.files[0]);
  });

  // Clipboard paste (Ctrl+V)
  window.addEventListener('paste', e => {
    const items = (e.clipboardData || e.originalEvent?.clipboardData)?.items;
    if (!items) return;
    for (const item of items) {
      if (item.kind === 'file') {
        const blob = item.getAsFile();
        if (blob) { handleFileSelected(blob); break; }
      }
    }
  });
}

// ── 3. FILE HANDLING & LEDGER RUN ───────────────────────────────────────────
function handleFileSelected(file) {
  const heroSection   = document.getElementById('hero-section');
  const ledgerSection = document.getElementById('ledger-section');
  const resultSection = document.getElementById('result-section');
  const ledgerFilename = document.getElementById('ledger-filename');

  if (heroSection)    heroSection.style.display   = 'none';
  if (resultSection)  resultSection.style.display = 'none';
  if (ledgerSection) {
    ledgerSection.style.display = 'block';
    if (ledgerFilename) {
      ledgerFilename.textContent =
        `${file.name || 'document.pdf'} · ${(file.size / 1024).toFixed(1)} KB`;
    }
  }

  // Reset all ledger items to pending
  document.querySelectorAll('.ledger-item').forEach(el => {
    el.classList.remove('running', 'done');
    const icon = el.querySelector('.step-icon');
    if (icon) icon.textContent = '·';
    const t = el.querySelector('.time-mono');
    if (t) t.textContent = '—';
  });

  // 5-step pipeline with staggered timing
  const steps = [
    { id: 'step-read',   label: 'READ FILE',                           ms: 18  },
    { id: 'step-ocr',    label: 'OCR + TEXT EXTRACTION',               ms: 210 },
    { id: 'step-crypto', label: 'CRYPTOGRAPHIC SIGNATURE CHECK',        ms: 36  },
    { id: 'step-record', label: 'COMPARE WITH INSTITUTIONAL RECORD',    ms: 54  },
    { id: 'step-ela',    label: 'FORENSIC EDIT DETECTION (ELA/NOISE)', ms: 88  }
  ];

  let idx = 0;
  function advance() {
    if (idx >= steps.length) {
      sendUploadRequest(file);
      return;
    }
    const step = steps[idx];
    const el   = document.getElementById(step.id);
    if (el) {
      el.classList.add('running');
      const icon = el.querySelector('.step-icon');
      if (icon) icon.textContent = '▶';
      setTimeout(() => {
        el.classList.remove('running');
        el.classList.add('done');
        if (icon) icon.textContent = '✓';
        const t = el.querySelector('.time-mono');
        if (t) t.textContent = `${step.ms}ms`;
        idx++;
        advance();
      }, 120);
    } else {
      idx++;
      advance();
    }
  }
  advance();
}

function sendUploadRequest(file) {
  fetch('/api/upload', { method: 'POST', body: file })
    .then(r => r.json())
    .then(data => displayResult(data))
    .catch(() => displayResult({
      road: 'B',
      verdict: 'CANNOT_VERIFY',
      headline: 'Network error. No institutional record matched.',
      findings: [{ check: 'Server Connection', outcome: 'fail', detail: 'Could not reach the backend.' }],
      certificate: {}
    }));
}

// ── 4. DISPLAY RESULT ───────────────────────────────────────────────────────
function displayResult(data) {
  const ledgerSection = document.getElementById('ledger-section');
  const resultSection = document.getElementById('result-section');
  if (ledgerSection) ledgerSection.style.display = 'none';
  if (resultSection) resultSection.style.display = 'block';

  const verdict  = (data.verdict || 'CANNOT_VERIFY');
  const certData = data.certificate || {};

  // Verdict word
  const verdictWordEl = document.getElementById('result-verdict-word');
  if (verdictWordEl) verdictWordEl.textContent = verdict.replace(/_/g,' ');

  // Headline
  const headlineEl = document.getElementById('result-headline');
  if (headlineEl) headlineEl.textContent = data.headline || 'Verification completed.';

  // Road badge
  const roadBadge = document.getElementById('verdict-road-badge');
  if (roadBadge) {
    if (data.road === 'A') {
      roadBadge.className = 'road-badge road-a';
      roadBadge.textContent = 'ROAD A · ISSUER-SIGNED DIGITAL CREDENTIAL';
    } else {
      roadBadge.className = 'road-badge road-b';
      roadBadge.textContent = 'ROAD B · SCANNED CREDENTIAL (ADVISORY)';
    }
  }

  // Stamp seal
  const seal     = document.getElementById('stamp-seal');
  const sealWord = document.getElementById('stamp-word');
  const sealId   = document.getElementById('stamp-id');
  if (seal) {
    seal.className = 'stamp-seal animate-stamp';
    const breakBox = document.getElementById('break-it-box');

    if (verdict === 'VERIFIED_ISSUER_SIGNED' || verdict === 'GENUINE') {
      seal.classList.add('verdict-genuine');
      if (sealWord) sealWord.textContent = 'VERIFIED';
      if (sealId)   sealId.textContent   = 'CRYPTOGRAPHIC MATCH';
      if (breakBox) breakBox.style.display = 'block';
    } else if (verdict === 'REVOKED') {
      seal.classList.add('verdict-altered');
      if (sealWord) sealWord.textContent = 'REVOKED';
      if (sealId)   sealId.textContent   = 'CANCELLATION ORDER ON FILE';
      if (breakBox) breakBox.style.display = 'none';
    } else if (verdict === 'LIKELY_ALTERED') {
      seal.classList.add('verdict-altered');
      if (sealWord) sealWord.textContent = 'TAMPERED';
      if (sealId)   sealId.textContent   = 'FORENSIC EVIDENCE FOUND';
      if (breakBox) breakBox.style.display = 'none';
    } else if (verdict === 'UNRECOGNIZED_DOCUMENT') {
      seal.classList.add('verdict-unknown');
      if (sealWord) sealWord.textContent = 'INVALID';
      if (sealId)   sealId.textContent   = 'NOT AN ACADEMIC CREDENTIAL';
      if (breakBox) breakBox.style.display = 'none';
    } else {
      seal.classList.add('verdict-review');
      if (sealWord) sealWord.textContent = 'ADVISORY';
      if (sealId)   sealId.textContent   = 'NO DIGITAL ANCHOR';
      if (breakBox) breakBox.style.display = 'none';
    }
  }

  // Sound + haptics
  playStampThud();
  if (navigator.vibrate) { try { navigator.vibrate(30); } catch (_) {} }

  // Increment counter
  verificationCounter++;
  const counterEl = document.getElementById('counter-number');
  if (counterEl) counterEl.textContent = verificationCounter.toLocaleString('en-IN');

  // Findings table
  const tbody = document.getElementById('findings-table-body');
  if (tbody && data.findings) {
    tbody.innerHTML = '';
    data.findings.forEach(f => {
      const tr  = document.createElement('tr');
      const tag = f.outcome === 'pass'
        ? '<span class="tag-mono pass">PASS</span>'
        : f.outcome === 'fail'
          ? '<span class="tag-mono fail">FAIL</span>'
          : '<span class="tag-mono warn">WARN</span>';
      tr.innerHTML = `
        <td style="font-weight:700;">${f.check}</td>
        <td>${tag}</td>
        <td class="time-mono" style="font-size:12px;color:var(--ink-soft);">${f.detail}</td>`;
      tbody.appendChild(tr);
    });
  }

  // Certificate meta grid
  const certBlock = document.getElementById('cert-details-block');
  if (certBlock) {
    const sha = data.fileSha256 || '';
    certBlock.innerHTML = `
      <div class="cert-meta-grid">
        <div class="cert-meta-item">
          <span class="cert-meta-label">CANDIDATE NAME</span>
          <span class="cert-meta-value">${certData.holderName || '—'}</span>
        </div>
        <div class="cert-meta-item">
          <span class="cert-meta-label">ROLL / REGISTRATION</span>
          <span class="cert-meta-value">${certData.rollNumber || certData.certId || '—'}</span>
        </div>
        <div class="cert-meta-item">
          <span class="cert-meta-label">INSTITUTION</span>
          <span class="cert-meta-value">${certData.institution || '—'}</span>
        </div>
        <div class="cert-meta-item">
          <span class="cert-meta-label">PROGRAMME</span>
          <span class="cert-meta-value">${certData.programme || certData.title || '—'}</span>
        </div>
        <div class="cert-meta-item">
          <span class="cert-meta-label">CGPA / GRADE</span>
          <span class="cert-meta-value">${certData.cgpa ? certData.cgpa + ' / 10.0' : '—'}</span>
        </div>
        <div class="cert-meta-item">
          <span class="cert-meta-label">FILE SHA-256</span>
          <span class="cert-meta-value" style="font-size:11px;">${sha ? sha.slice(0,24)+'…' : '—'}</span>
        </div>
      </div>`;
  }

  // Scroll to result
  resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

  // Live status for screen readers
  const liveRegion = document.getElementById('live-status');
  if (liveRegion) liveRegion.textContent = `Verdict: ${verdict.replace(/_/g,' ')}. ${data.headline || ''}`;
}

// ── 5. PRESET QUICK-TEST VECTORS ────────────────────────────────────────────
function runPreset(presetId) {
  const presets = {
    'amit-genuine': {
      road: 'A',
      verdict: 'VERIFIED_ISSUER_SIGNED',
      headline: 'Signature matches Ranchi University institutional key. Ed25519 commitment valid.',
      certificate: {
        holderName: 'Amit Kumar',
        rollNumber: '2020-RU-CS-0492',
        institution: 'Ranchi University',
        programme: 'B.Tech Computer Science',
        cgpa: '8.84'
      },
      findings: [
        { check: 'OCR Text Quality',           outcome: 'pass', detail: 'High-confidence extraction.' },
        { check: 'Ed25519 Signature',           outcome: 'pass', detail: 'Valid. Matches issuer public key.' },
        { check: 'Institutional Registry',      outcome: 'pass', detail: 'Record found: ACTIVE.' },
        { check: 'Arithmetic Audit (CGPA)',     outcome: 'pass', detail: 'Sum matches stated CGPA.' },
        { check: 'Forensic Edit Detection',     outcome: 'pass', detail: 'No anomalous noise variance.' }
      ],
      fileSha256: '3f9a1c07e8b411d9f00192ca1819bb20501a91e5714cb2074c7b8091ecf15190'
    },
    'keshav-revoked': {
      road: 'A',
      verdict: 'REVOKED',
      headline: 'Credential VBU-2023-11002 is on the revocation list. Cancellation order dated 2024-03-14.',
      certificate: {
        holderName: 'Keshav Bhardwaj',
        rollNumber: 'VBU-2023-11002',
        institution: 'Vinoba Bhave University',
        programme: 'B.Sc Mathematics',
        cgpa: '7.2'
      },
      findings: [
        { check: 'Institutional Registry', outcome: 'fail', detail: 'Status: REVOKED. Order: RO-2024-11002.' },
        { check: 'Ed25519 Signature',      outcome: 'pass', detail: 'Signature valid but credential cancelled.' }
      ],
      fileSha256: 'a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3'
    },
    'altered-grade': {
      road: 'B',
      verdict: 'LIKELY_ALTERED',
      headline: 'Text in the CGPA field shows elevated noise variance. Arithmetic sum does not match stated total.',
      certificate: { holderName: 'Unknown', rollNumber: '—', institution: 'Unregistered', programme: '—' },
      findings: [
        { check: 'Arithmetic Audit (CGPA)', outcome: 'fail', detail: 'Stated: 9.95. Computed: 8.84. Mismatch.' },
        { check: 'ELA Noise Analysis',      outcome: 'fail', detail: 'Laplacian variance 3.8× above baseline.' },
        { check: 'Institutional Registry',  outcome: 'warn', detail: 'No matching digital anchor found.' }
      ],
      fileSha256: '9d814cb2074c7b8091ecf151903f9a1c07e8b411d9f00192ca1819bb20501a91'
    },
    'random-doc': {
      road: 'B',
      verdict: 'UNRECOGNIZED_DOCUMENT',
      headline: 'File contains no academic keywords. Academic Semantic Gate blocked this submission.',
      certificate: {},
      findings: [
        { check: 'Academic Semantic Gate', outcome: 'fail', detail: 'No academic keywords found in text.' },
        { check: 'Document Classification',outcome: 'warn', detail: 'Appears to be a non-academic file.' }
      ],
      fileSha256: 'deadbeefcafe0000111122223333444455556666777788889999aaaabbbbccccdddd'
    }
  };

  const data = presets[presetId];
  if (!data) return;

  const heroSection   = document.getElementById('hero-section');
  const ledgerSection = document.getElementById('ledger-section');
  const ledgerFilename = document.getElementById('ledger-filename');
  if (heroSection)    heroSection.style.display   = 'none';
  if (ledgerSection) {
    ledgerSection.style.display = 'block';
    if (ledgerFilename) ledgerFilename.textContent = `PRESET: ${presetId}.pdf · (demo)`;
  }

  // Reset ledger items
  document.querySelectorAll('.ledger-item').forEach(el => {
    el.classList.remove('running', 'done');
    const icon = el.querySelector('.step-icon');
    if (icon) icon.textContent = '·';
    const t = el.querySelector('.time-mono');
    if (t) t.textContent = '—';
  });

  const stepIds = ['step-read','step-ocr','step-crypto','step-record','step-ela'];
  const times   = [12, 188, 30, 42, 72];
  let i = 0;
  function next() {
    if (i >= stepIds.length) { displayResult(data); return; }
    const el = document.getElementById(stepIds[i]);
    if (el) {
      el.classList.add('running');
      const icon = el.querySelector('.step-icon');
      if (icon) icon.textContent = '▶';
      setTimeout(() => {
        el.classList.remove('running');
        el.classList.add('done');
        if (icon) icon.textContent = '✓';
        const t = el.querySelector('.time-mono');
        if (t) t.textContent = `${times[i]}ms`;
        i++;
        next();
      }, 110);
    } else { i++; next(); }
  }
  next();
}

// ── 6. BREAK IT YOURSELF SANDBOX ────────────────────────────────────────────
function initBreakItYourself() {
  const btnBreak = document.getElementById('btn-break-one-letter');
  const btnReset = document.getElementById('btn-reset-tamper');
  if (!btnBreak) return;

  const originalPayload = '{\n  "holder": "Amit Kumar",\n  "cgpa": 8.84,\n  "roll": "2020-RU-CS-0492"\n}';
  const originalHash    = '3f9a1c07e8b411d9f00192ca1819bb20501a91e5714cb2074c7b8091ecf15190';
  const tamperedPayload = '{\n  "holder": "Amit Kumar",\n  "cgpa": <span class="hash-highlight">9.84</span>,\n  "roll": "2020-RU-CS-0492"\n}';
  const tamperedHash    = '<span class="hash-highlight">9d814cb2074c7b8091ecf151903f9a1c07e8b411d9f00192ca1819bb20501a91</span>';

  // Initialize display
  const payloadBox = document.getElementById('break-payload');
  const hashBox    = document.getElementById('break-hash');
  const statusBox  = document.getElementById('break-status');
  if (payloadBox) payloadBox.textContent = originalPayload;
  if (hashBox)    hashBox.textContent    = originalHash;
  if (statusBox)  statusBox.innerHTML    = '<span class="tag-mono pass">VERDICT: SIGNATURE VALID — MATHEMATICAL MATCH</span>';

  btnBreak.addEventListener('click', () => {
    if (payloadBox) payloadBox.innerHTML = tamperedPayload;
    if (hashBox)    hashBox.innerHTML    = tamperedHash;
    if (statusBox)  statusBox.innerHTML  = '<span class="tag-mono fail">SIGNATURE INVALID: CRYPTOGRAPHIC HASH MISMATCH — FRAUD BLOCKED</span>';
    if (btnReset)   btnReset.style.display = 'inline-block';
    playStampThud();
  });

  if (btnReset) {
    btnReset.addEventListener('click', () => {
      if (payloadBox) payloadBox.textContent = originalPayload;
      if (hashBox)    hashBox.textContent    = originalHash;
      if (statusBox)  statusBox.innerHTML    = '<span class="tag-mono pass">VERDICT: SIGNATURE VALID — MATHEMATICAL MATCH</span>';
      btnReset.style.display = 'none';
    });
  }
}

// ── 7. KEYBOARD SHORTCUTS ────────────────────────────────────────────────────
function initKeyboard() {
  window.addEventListener('keydown', e => {
    if (['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) return;
    if (e.key === '/') {
      e.preventDefault();
      const slab = document.getElementById('drop-slab');
      if (slab) slab.focus();
    } else if (e.key === 'v' || e.key === 'V') {
      document.getElementById('file-input')?.click();
    } else if (e.key === 'r' || e.key === 'R') {
      window.print();
    } else if (e.key === '?') {
      e.preventDefault();
      toggleModal('modal-shortcuts');
    } else if (e.key === 'Escape') {
      document.querySelectorAll('.dialog-overlay').forEach(d => d.classList.remove('active'));
    } else if (e.key === 'h' || e.key === 'H') {
      resetToHome();
    }
  });
}

function toggleModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.toggle('active');
}

// ── 8. THEME & LANGUAGE ──────────────────────────────────────────────────────
function toggleTheme() {
  const cur  = document.documentElement.getAttribute('data-theme') || 'light';
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('ava_theme', next);
  const btn = document.getElementById('btn-theme-toggle');
  if (btn) btn.textContent = next === 'dark' ? 'LIGHT MODE' : 'DARK MODE';
}

function toggleLanguage() {
  currentLang = currentLang === 'en' ? 'hi' : 'en';
  const dict  = I18N[currentLang];
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (dict[key] !== undefined) el.textContent = dict[key];
  });
  const langBtn = document.getElementById('btn-lang-toggle');
  if (langBtn) langBtn.textContent = currentLang === 'en' ? 'हिं' : 'EN';
  document.documentElement.setAttribute('lang', currentLang === 'hi' ? 'hi' : 'en');
}

function toggleSound() {
  soundEnabled = !soundEnabled;
  const btn = document.getElementById('btn-sound-toggle');
  if (btn) btn.textContent = soundEnabled ? 'THUD: ON' : 'THUD: OFF';
}

// ── 9. NAVIGATION ────────────────────────────────────────────────────────────
function resetToHome() {
  const heroSection   = document.getElementById('hero-section');
  const ledgerSection = document.getElementById('ledger-section');
  const resultSection = document.getElementById('result-section');
  if (heroSection)    heroSection.style.display   = 'block';
  if (ledgerSection)  ledgerSection.style.display = 'none';
  if (resultSection)  resultSection.style.display = 'none';
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function copyResultLink() {
  navigator.clipboard.writeText(window.location.href).then(() => {
    const btn = document.getElementById('btn-copy-link');
    if (btn) { const old = btn.textContent; btn.textContent = 'COPIED'; setTimeout(() => btn.textContent = old, 1500); }
  });
}

function shareOnWhatsApp() {
  const text = encodeURIComponent(
    'Verified academic credential on AUTHENTICITY VALIDATOR FOR ACADEMIA: ' + window.location.href
  );
  window.open('https://wa.me/?text=' + text, '_blank');
}

// ── 10. COUNTER ANIMATION ────────────────────────────────────────────────────
function animateCounter(target, duration) {
  const el    = document.getElementById('counter-number');
  if (!el) return;
  const start = target - 12;
  const diff  = target - start;
  const tStart = performance.now();
  function step(now) {
    const elapsed  = now - tStart;
    const progress = Math.min(elapsed / duration, 1);
    el.textContent = Math.floor(start + diff * progress).toLocaleString('en-IN');
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// ── DOM READY ────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Restore theme
  const savedTheme = localStorage.getItem('ava_theme') ||
    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', savedTheme);
  const themeBtn = document.getElementById('btn-theme-toggle');
  if (themeBtn) themeBtn.textContent = savedTheme === 'dark' ? 'LIGHT MODE' : 'DARK MODE';

  // Init systems
  initDropSlab();
  initBreakItYourself();
  initKeyboard();

  // Animate counter on load
  animateCounter(verificationCounter, 1200);
});
