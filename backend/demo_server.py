"""Full Production Demo Server integrating:
- Mohar Guilloche mathematical seal rendering
- Section 8.5 Verification Ledger
- Section 6.5 Exact Verdict Headlines & Copy
- Bilingual Language Switch (English & Hindi)
- Theme Switching (Paper Light / Night Press Dark)
- Responsive Layout with Netflix UX principles
"""

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time
import math

from backend.app.modules.crypto.canonical import canonicalize_json
from backend.app.modules.crypto.signer import Ed25519Signer
from backend.app.modules.crypto.merkle import MerkleTree, hash_leaf
from backend.app.modules.verify.engine import verify_road_a_pipeline, VerdictCode
from backend.app.modules.forensics.pipeline import (
    analyze_pdf_metadata, analyze_noise_consistency, analyze_glyph_consistency,
    analyze_copy_move, evaluate_road_b_verdict
)

app = FastAPI(title="Sanad - Authenticity Validator Full UI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo Signer and Institutions
DEMO_SIGNER = Ed25519Signer()
DEMO_INSTITUTION = {
    "id": "inst_01",
    "name": "Demo Institute of Technology (sample, not a real institution)",
    "official_domain": "demo-tech.ac.in",
    "status": "approved",
    "approved_at": "2026-03-02T10:00:00Z"
}

# 1. Genuine Digital Certificate
payload_genuine = {
    "schema": "sanad.cert/1",
    "certificateId": "SND-7K3Q9M2XW4PTH8RA",
    "issuer": {"institutionId": DEMO_INSTITUTION["id"], "keyId": DEMO_SIGNER.key_id},
    "holder": {"name": "Rohan Sharma (रोहन शर्मा)", "enrolmentNoHash": "sha256:d5a1..."},
    "credential": {
        "title": "Bachelor of Technology",
        "programme": "Computer Science and Engineering",
        "level": "UG",
        "result": {"cgpa": 8.42, "division": "First"},
        "issuedOn": "2026-07-15",
        "sessionYears": "2022-2026"
    },
    "supersedes": None
}
canonical_genuine = canonicalize_json(payload_genuine)
sig_genuine = DEMO_SIGNER.sign(canonical_genuine)
leaf_genuine = hash_leaf(canonical_genuine)
merkle_tree = MerkleTree([leaf_genuine, hash_leaf(b"batch_leaf_2")])

# 2. Revoked Certificate
payload_revoked = {
    "schema": "sanad.cert/1",
    "certificateId": "SND-REVOKED9999999",
    "issuer": {"institutionId": DEMO_INSTITUTION["id"], "keyId": DEMO_SIGNER.key_id},
    "holder": {"name": "Priya Verma (प्रिया वर्मा)", "enrolmentNoHash": "sha256:f12b..."},
    "credential": {
        "title": "Bachelor of Technology",
        "programme": "Electrical Engineering",
        "level": "UG",
        "result": {"cgpa": 7.15, "division": "First"},
        "issuedOn": "2026-05-10",
        "sessionYears": "2022-2026"
    },
    "supersedes": None
}
canonical_revoked = canonicalize_json(payload_revoked)
sig_revoked = DEMO_SIGNER.sign(canonical_revoked)

class MockRecord:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

CERTIFICATES_DB = {
    "SND-7K3Q9M2XW4PTH8RA": MockRecord(
        certificate_id="SND-7K3Q9M2XW4PTH8RA",
        key_id=DEMO_SIGNER.key_id,
        canonical_payload=canonical_genuine,
        signature=sig_genuine,
        payload_json=payload_genuine,
        holder_name="Rohan Sharma",
        status="issued"
    ),
    "SND-REVOKED9999999": MockRecord(
        certificate_id="SND-REVOKED9999999",
        key_id=DEMO_SIGNER.key_id,
        canonical_payload=canonical_revoked,
        signature=sig_revoked,
        payload_json=payload_revoked,
        holder_name="Priya Verma",
        status="revoked"
    )
}

REVOCATIONS_DB = {
    "SND-REVOKED9999999": MockRecord(
        certificate_id="SND-REVOKED9999999",
        reason_code="DEGREE_WITHDRAWN",
        revoked_at="2026-08-01T14:30:00Z"
    )
}

BATCH_RECORD = MockRecord(
    batch_id=481,
    anchor_kind="evm-testnet",
    anchor_receipt={"transparency_root": merkle_tree.root_hex, "leaf_count": 2},
    anchored_at=time.time()
)


def generate_mohar_svg(hash_hex: str, verdict: str, size: int = 240) -> str:
    """Generate deterministic Mohar guilloche SVG directly from hash string."""
    h_bytes = bytes.fromhex(hash_hex) if len(hash_hex) >= 64 else b"\x00" * 32
    cx, cy = 120, 120
    r_outer = 115

    # Ring code 96 ticks
    ticks = []
    for i in range(96):
        b_idx = i // 8
        bit_idx = 7 - (i % 8)
        is_set = ((h_bytes[b_idx % len(h_bytes)] >> bit_idx) & 1) == 1
        t_len = 6 if is_set else 3
        ang = (2 * math.pi * i) / 96
        x1 = round(cx + (r_outer - t_len) * math.cos(ang), 2)
        y1 = round(cy + (r_outer - t_len) * math.sin(ang), 2)
        x2 = round(cx + r_outer * math.cos(ang), 2)
        y2 = round(cy + r_outer * math.sin(ang), 2)
        ticks.append(f"M{x1},{y1}L{x2},{y2}")

    # Rosette layers
    layers = [
        {"R": 100, "lobe": h_bytes[12] if len(h_bytes) > 12 else 7, "d": h_bytes[15] if len(h_bytes) > 15 else 128},
        {"R": 78, "lobe": h_bytes[13] if len(h_bytes) > 13 else 9, "d": h_bytes[16] if len(h_bytes) > 16 else 128},
        {"R": 56, "lobe": h_bytes[14] if len(h_bytes) > 14 else 11, "d": h_bytes[17] if len(h_bytes) > 17 else 128},
    ]
    coprimes = [5, 7, 8, 9, 11, 13, 15, 17]
    paths = []
    is_advisory = verdict.startswith("CONSISTENT") or verdict.startswith("NEEDS") or verdict.startswith("LIKELY")

    for idx, lay in enumerate(layers):
        n = coprimes[lay["lobe"] % len(coprimes)]
        r = (lay["R"] * (n - 1)) / n
        d = 0.45 * r + (0.45 * r * lay["d"]) / 255.0
        steps = 140
        pts = []
        rot = (idx * 0.4) if verdict != "INVALID_SIGNATURE" else (idx * 1.5)
        for s in range(steps + 1):
            t = (2 * math.pi * s) / steps
            arg = ((lay["R"] - r) / r) * t + rot
            x = round(cx + (lay["R"] - r) * math.cos(t + rot) + d * math.cos(arg), 2)
            y = round(cy + (lay["R"] - r) * math.sin(t + rot) - d * math.sin(arg), 2)
            pts.append(f"{'M' if s == 0 else 'L'}{x},{y}")
        pts.append("Z")
        paths.append("".join(pts))

    notch = '<path d="M112,5 A115,115 0 0,1 128,5" fill="none" stroke="var(--sindoor, #C2412D)" stroke-width="3.5" stroke-linecap="round"/>' if verdict == "VERIFIED_ISSUER_SIGNED" else ""
    cut = '<line x1="20" y1="220" x2="220" y2="20" stroke="var(--sindoor, #C2412D)" stroke-width="2.5" stroke-linecap="round"/>' if verdict == "REVOKED" else ""
    center_text = "ADVISORY" if is_advisory else "SANAD"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="{size}" height="{size}" role="img" aria-label="Mohar Seal">
      <g stroke="currentColor" fill="none">
        <path d="{''.join(ticks)}" stroke-width="0.8" opacity="0.75"/>
        {''.join([f'<path d="{p}" stroke-width="0.7" stroke-dasharray="{"2 3" if is_advisory else "none"}" opacity="0.85"/>' for p in paths])}
        {notch}
        <circle cx="{cx}" cy="{cy}" r="22" fill="var(--bg-surface, #F3EDDD)" stroke="currentColor" stroke-width="1.2"/>
        <text x="{cx}" y="{cy + 4}" font-family="Fraunces, Georgia, serif" font-size="{"8" if is_advisory else "11"}" font-weight="bold" fill="currentColor" text-anchor="middle">{center_text}</text>
        {cut}
      </g>
    </svg>"""


@app.get("/api/v1/verify/{certificate_id}")
async def verify_endpoint(certificate_id: str):
    cert = CERTIFICATES_DB.get(certificate_id)
    inst = MockRecord(**DEMO_INSTITUTION)
    key = MockRecord(key_id=DEMO_SIGNER.key_id, public_key=DEMO_SIGNER.public_key_hex, status="active")
    rev = REVOCATIONS_DB.get(certificate_id)

    res = verify_road_a_pipeline(
        cert_record=cert,
        inst_record=inst if cert else None,
        key_record=key if cert else None,
        revocation_record=rev,
        batch_record=BATCH_RECORD if cert else None
    )
    data = res.dict()
    data["moharSvg"] = generate_mohar_svg(cert.canonical_payload.hex() if cert else "0" * 64, data["verdict"])
    return data


@app.get("/api/v1/verify/road-b-demo")
async def verify_road_b_demo(scenario: str = "clean"):
    if scenario == "altered":
        verdict, summary, findings = evaluate_road_b_verdict(
            registry_matched=True,
            field_discrepancies=["Marks/CGPA extracted 9.80 contradicts institution registry 7.40"],
            forensic_signals=[
                analyze_pdf_metadata(b"Adobe Photoshop CC 2024 %%EOF %%EOF"),
                analyze_glyph_consistency(1.35)
            ]
        )
    else:
        verdict, summary, findings = evaluate_road_b_verdict(
            registry_matched=True,
            field_discrepancies=[],
            forensic_signals=[
                analyze_pdf_metadata(b"Sanad Native Engine %%EOF"),
                analyze_noise_consistency(0.02),
                analyze_glyph_consistency(1.0),
                analyze_copy_move(0)
            ]
        )
    return {
        "road": "B",
        "verdict": verdict,
        "summary": summary,
        "findings": findings,
        "moharSvg": generate_mohar_svg("b" * 64, verdict),
        "notice": "Road B verdicts are strictly probabilistic & advisory. Never treated as mathematical proof."
    }


@app.get("/", response_class=HTMLResponse)
async def full_ui():
    return """
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sanad · Authenticity Validator for Academia</title>
  <style>
    :root {
      --paper-50: #FAF6EC;
      --paper-100: #F3EDDD;
      --paper-200: #E7DFC9;
      --ink-900: #15191F;
      --ink-700: #3A424D;
      --ink-500: #66707C;
      --neel: #1F2F5C;
      --sindoor: #C2412D;
      --haldi: #D8A238;
      --verified: #1E6B4A;
      --caution: #9A5B00;
      --danger: #B3261E;
      --neutral: #5B6572;

      --bg-page: var(--paper-50);
      --bg-surface: var(--paper-100);
      --border-hairline: var(--paper-200);
      --text-main: var(--ink-900);
      --text-secondary: var(--ink-700);
    }
    [data-theme="dark"] {
      --bg-page: #0F1318;
      --bg-surface: #161B22;
      --border-hairline: #2B3440;
      --text-main: #ECE7DA;
      --text-secondary: #AEB6C2;
      --neel: #8FA6E8;
      --sindoor: #E8674F;
      --verified: #62C08D;
      --caution: #E6B35A;
      --danger: #F08A80;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 0;
      background-color: var(--bg-page);
      color: var(--text-main);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.6;
      transition: background-color 200ms ease, color 200ms ease;
    }
    .header-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 24px;
      border-bottom: 1px solid var(--border-hairline);
      background: var(--bg-surface);
    }
    .brand-mark {
      font-family: Georgia, serif;
      font-size: 20px;
      font-weight: bold;
      color: var(--text-main);
      text-decoration: none;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .controls { display: flex; gap: 12px; align-items: center; }
    .theme-toggle, .lang-toggle {
      background: none;
      border: 1px solid var(--border-hairline);
      padding: 6px 12px;
      font-size: 13px;
      border-radius: 4px;
      color: var(--text-main);
      cursor: pointer;
    }
    .container {
      max-width: 1040px;
      margin: 40px auto;
      padding: 0 20px;
    }
    .hero-split {
      display: grid;
      grid-template-columns: 1fr 300px;
      gap: 40px;
      align-items: center;
      margin-bottom: 48px;
    }
    @media (max-width: 800px) {
      .hero-split { grid-template-columns: 1fr; }
    }
    h1 {
      font-family: Georgia, serif;
      font-size: 34px;
      line-height: 1.25;
      margin: 0 0 16px 0;
      color: var(--text-main);
    }
    p.lead {
      font-size: 16px;
      color: var(--text-secondary);
      margin: 0 0 24px 0;
    }
    .verify-box {
      display: flex;
      gap: 8px;
      margin-bottom: 12px;
    }
    .verify-input {
      flex: 1;
      padding: 14px 16px;
      font-size: 15px;
      font-family: monospace;
      border: 1px solid var(--border-hairline);
      border-radius: 6px;
      background: var(--bg-surface);
      color: var(--text-main);
    }
    .btn-verify {
      padding: 14px 28px;
      background: var(--neel);
      color: #FFF;
      font-weight: 600;
      border: none;
      border-radius: 6px;
      cursor: pointer;
    }
    .shelf-title {
      font-size: 18px;
      font-weight: bold;
      margin: 32px 0 16px 0;
      display: flex;
      justify-content: space-between;
      align-items: baseline;
    }
    .scenarios-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 40px;
    }
    .card-scenario {
      border: 1px solid var(--border-hairline);
      background: var(--bg-surface);
      border-radius: 6px;
      padding: 18px;
      cursor: pointer;
      transition: transform 160ms ease, box-shadow 160ms ease;
    }
    .card-scenario:hover {
      transform: translateY(-3px);
      box-shadow: 0 8px 24px rgba(0,0,0,0.06);
    }
    .card-tag {
      font-size: 11px;
      font-weight: bold;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      color: var(--sindoor);
      margin-bottom: 8px;
    }
    
    /* Result Section */
    #result-panel {
      display: none;
      border: 1px solid var(--border-hairline);
      border-radius: 8px;
      background: var(--bg-surface);
      padding: 32px;
      margin-top: 32px;
    }
    .result-grid {
      display: grid;
      grid-template-columns: 240px 1fr;
      gap: 32px;
    }
    @media (max-width: 768px) {
      .result-grid { grid-template-columns: 1fr; }
    }
    .verdict-badge {
      display: inline-block;
      font-weight: bold;
      font-size: 15px;
      padding: 6px 16px;
      border-radius: 4px;
      margin-bottom: 12px;
    }
    .VERIFIED_ISSUER_SIGNED { background: #EBF8F2; color: #0E6245; }
    .REVOKED, .LIKELY_ALTERED, .INVALID_SIGNATURE { background: #FDF2F2; color: #A71D2A; }
    .CONSISTENT_WITH_REGISTRY { background: #FEF8E7; color: #8A6100; }
    
    .ledger-row {
      display: flex;
      justify-content: space-between;
      padding: 10px 14px;
      background: var(--bg-page);
      border: 1px solid var(--border-hairline);
      border-radius: 4px;
      margin-bottom: 8px;
      font-size: 13px;
    }
  </style>
</head>
<body>

  <header class="header-bar">
    <a href="/" class="brand-mark">
      <span>मुहर · Sanad</span>
    </a>
    <div class="controls">
      <button class="lang-toggle" onclick="toggleLang()" id="btn-lang">हिंदी</button>
      <button class="theme-toggle" onclick="toggleTheme()" id="btn-theme">Night Press</button>
    </div>
  </header>

  <div class="container">
    <div class="hero-split">
      <div>
        <h1 id="txt-headline">Check a certificate before you trust it.</h1>
        <p class="lead" id="txt-lead">
          Scan the QR on the page, type its ID, or upload a scan. You get a clear answer, and the reasons behind it.
        </p>
        <div class="verify-box">
          <input type="text" class="verify-input" id="inp-cert" placeholder="Certificate ID, like SND-7K3Q…" value="SND-7K3Q9M2XW4PTH8RA" />
          <button class="btn-verify" onclick="verifyEnteredId()" id="txt-btn-verify">Check certificate</button>
        </div>
        <div style="font-size: 13px; color: var(--text-secondary);" id="txt-reassurance">
          No sign-in needed. Uploaded scans are deleted after 30 days.
        </div>
      </div>
      <div style="text-align: center;" id="hero-seal-slot">
        <!-- Live Inked Mohar -->
      </div>
    </div>

    <div class="shelf-title">
      <span id="txt-shelf">Interactive Verification Scenarios</span>
      <span style="font-size: 12px; font-weight: normal; color: var(--text-secondary);">Real pipeline execution</span>
    </div>

    <div class="scenarios-grid">
      <div class="card-scenario" onclick="runCheck('SND-7K3Q9M2XW4PTH8RA')">
        <div class="card-tag">Road A · Cryptographic</div>
        <strong>1. Genuine Digital Degree</strong>
        <p style="font-size: 13px; margin: 6px 0 0 0; color: var(--text-secondary);">Ed25519 signature verified, Merkle batch anchored.</p>
      </div>

      <div class="card-scenario" onclick="runCheck('SND-REVOKED9999999')">
        <div class="card-tag">Road A · Revocation</div>
        <strong>2. Revoked Credential</strong>
        <p style="font-size: 13px; margin: 6px 0 0 0; color: var(--text-secondary);">Withdrawn by the institution. Diagonal seal cut.</p>
      </div>

      <div class="card-scenario" onclick="runRoadB('clean')">
        <div class="card-tag">Road B · Advisory</div>
        <strong>3. Legacy Scanned Paper (Clean)</strong>
        <p style="font-size: 13px; margin: 6px 0 0 0; color: var(--text-secondary);">Matches registry. Advisory outline seal.</p>
      </div>

      <div class="card-scenario" onclick="runRoadB('altered')">
        <div class="card-tag">Road B · Forensics</div>
        <strong>4. Tampered Paper Scan</strong>
        <p style="font-size: 13px; margin: 6px 0 0 0; color: var(--text-secondary);">Contradicts registry & metadata editing detected.</p>
      </div>
    </div>

    <!-- Section 8.5 Verification Ledger Panel -->
    <section id="result-panel">
      <div class="result-grid">
        <div style="text-align: center;" id="result-mohar-box"></div>
        <div>
          <div id="result-badge-box"></div>
          <h2 id="result-headline" style="font-family: Georgia, serif; margin: 0 0 8px 0; font-size: 24px;"></h2>
          <p id="result-sentence" style="color: var(--text-secondary); margin: 0 0 20px 0; font-size: 15px;"></p>

          <div id="result-cert-box" style="padding: 16px; background: var(--bg-page); border: 1px solid var(--border-hairline); border-radius: 6px; margin-bottom: 24px;"></div>

          <h3 style="font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; margin: 0 0 12px 0;">
            Audit & Forensic Checks Ledger
          </h3>
          <div id="result-ledger-box"></div>
        </div>
      </div>
    </section>
  </div>

  <script>
    let currentLang = 'en';

    const STRINGS = {
      en: {
        headline: "Check a certificate before you trust it.",
        lead: "Scan the QR on the page, type its ID, or upload a scan. You get a clear answer, and the reasons behind it.",
        btnVerify: "Check certificate",
        reassurance: "No sign-in needed. Uploaded scans are deleted after 30 days.",
        shelf: "Interactive Verification Scenarios",
        langBtn: "हिंदी"
      },
      hi: {
        headline: "भरोसा करने से पहले प्रमाणपत्र जाँच लें।",
        lead: "पेज पर छपा QR स्कैन करें, उसकी ID लिखें, या स्कैन अपलोड करें। आपको साफ़ जवाब मिलेगा, और उसकी वजह भी।",
        btnVerify: "जाँचें",
        reassurance: "लॉगिन की ज़रूरत नहीं। अपलोड की गई फ़ाइलें 30 दिनों बाद हटा दी जाती हैं।",
        shelf: "सत्यापन परिदृश्य",
        langBtn: "English"
      }
    };

    function toggleTheme() {
      const html = document.documentElement;
      const isDark = html.getAttribute('data-theme') === 'dark';
      html.setAttribute('data-theme', isDark ? 'light' : 'dark');
      document.getElementById('btn-theme').innerText = isDark ? 'Night Press' : 'Paper Theme';
    }

    function toggleLang() {
      currentLang = currentLang === 'en' ? 'hi' : 'en';
      const s = STRINGS[currentLang];
      document.getElementById('txt-headline').innerText = s.headline;
      document.getElementById('txt-lead').innerText = s.lead;
      document.getElementById('txt-btn-verify').innerText = s.btnVerify;
      document.getElementById('txt-reassurance').innerText = s.reassurance;
      document.getElementById('txt-shelf').innerText = s.shelf;
      document.getElementById('btn-lang').innerText = s.langBtn;
    }

    async function runCheck(certId) {
      const res = await fetch('/api/v1/verify/' + certId);
      const data = await res.json();
      renderVerdict(data);
    }

    async function runRoadB(scenario) {
      const res = await fetch('/api/v1/verify/road-b-demo?scenario=' + scenario);
      const data = await res.json();
      renderVerdict(data);
    }

    function verifyEnteredId() {
      const val = document.getElementById('inp-cert').value.trim();
      if (val) runCheck(val);
    }

    function renderVerdict(data) {
      const panel = document.getElementById('result-panel');
      panel.style.display = 'block';
      panel.scrollIntoView({ behavior: 'smooth' });

      document.getElementById('result-mohar-box').innerHTML = data.moharSvg || '';
      document.getElementById('result-badge-box').innerHTML = 
        '<span class="verdict-badge ' + data.verdict + '">' + data.verdict + '</span>' +
        '<span style="float:right; font-size:12px; color:var(--text-secondary);">' + (data.durationMs ? data.durationMs + ' ms' : 'Advisory') + '</span>';

      document.getElementById('result-headline').innerText = 
        data.verdict === 'VERIFIED_ISSUER_SIGNED' ? 'Verified' :
        data.verdict === 'REVOKED' ? 'Withdrawn by the institution' :
        data.verdict === 'CONSISTENT_WITH_REGISTRY' ? 'Matches the record (advisory)' : 'Likely altered';

      document.getElementById('result-sentence').innerText = data.summary;

      const certBox = document.getElementById('result-cert-box');
      if (data.certificate) {
        certBox.style.display = 'block';
        certBox.innerHTML = 
          '<strong>Holder:</strong> ' + data.certificate.holderName + '<br/>' +
          '<strong>Degree:</strong> ' + data.certificate.title + ' in ' + data.certificate.programme + '<br/>' +
          '<strong>Issued On:</strong> ' + data.certificate.issuedOn + '<br/>' +
          '<strong>Institution:</strong> ' + (data.certificate.institutionName || 'Demo Institute of Technology');
      } else {
        certBox.style.display = 'none';
      }

      const ledger = document.getElementById('result-ledger-box');
      ledger.innerHTML = '';
      (data.findings || []).forEach(f => {
        const row = document.createElement('div');
        row.className = 'ledger-row';
        row.innerHTML = 
          '<span><strong>' + (f.check || f.signal_name) + ':</strong> ' + (f.detail || f.explanation) + '</span>' +
          '<strong style="color:' + (f.outcome === 'pass' ? 'var(--verified)' : 'var(--danger)') + '">' + (f.outcome || 'FLAGGED').toUpperCase() + '</strong>';
        ledger.appendChild(row);
      });
    }

    // Initialize hero seal
    window.addEventListener('DOMContentLoaded', () => {
      fetch('/api/v1/verify/SND-7K3Q9M2XW4PTH8RA')
        .then(r => r.json())
        .then(d => {
          document.getElementById('hero-seal-slot').innerHTML = d.moharSvg || '';
        });
    });
  </script>
</body>
</html>
    """
