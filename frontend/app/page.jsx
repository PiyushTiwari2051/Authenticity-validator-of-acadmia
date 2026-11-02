import React, { useState } from 'react';

// Design Tokens conform strictly to tokens.css: Paper & Ink palette
const PAPER_BG = '#FBFBFA';
const TEXT_INK = '#18181A';
const ACCENT_PRIMARY = '#1C355E';
const BORDER_SUBTLE = '#E2E2DC';

export default function HomeAndVerifyPage() {
  const [certId, setCertId] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleVerifyId = async (e) => {
    e.preventDefault();
    if (!certId.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`/api/v1/verify/${encodeURIComponent(certId.trim())}`);
      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || 'Verification request failed');
      }
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getVerdictBadgeStyle = (verdict) => {
    switch (verdict) {
      case 'VERIFIED_ISSUER_SIGNED':
        return { background: '#EBF8F2', color: '#0E6245', border: '1px solid #A3E3CA' };
      case 'VERIFIED_PENDING_ANCHOR':
        return { background: '#FEF8E7', color: '#8A6100', border: '1px solid #FBE297' };
      case 'REVOKED':
      case 'INVALID_SIGNATURE':
      case 'LIKELY_ALTERED':
        return { background: '#FDF2F2', color: '#A71D2A', border: '1px solid #F8B4B4' };
      default:
        return { background: '#F3F4F6', color: '#374151', border: '1px solid #D1D5DB' };
    }
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: PAPER_BG, color: TEXT_INK, fontFamily: 'serif', padding: '32px 16px' }}>
      <main style={{ maxWidth: '680px', margin: '0 auto', background: '#FFFFFF', border: `1px solid ${BORDER_SUBTLE}`, borderRadius: '8px', padding: '40px' }}>
        
        {/* Header */}
        <header style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{ fontSize: '13px', fontWeight: 'bold', letterSpacing: '1px', textTransform: 'uppercase', color: ACCENT_PRIMARY, marginBottom: '8px' }}>
            Sanad · प्रमाणन प्रणाली
          </div>
          <h1 style={{ fontSize: '28px', fontWeight: 'bold', margin: '0 0 12px 0' }}>
            Academic Credential Authenticity Validator
          </h1>
          <p style={{ fontSize: '14px', color: '#575759', lineHeight: '1.5', margin: 0 }}>
            Verifies digital certificates natively signed by registered academic institutions (Road A), 
            or runs multi-signal forensic checks on scanned paper documents (Road B).
          </p>
        </header>

        {/* Verification Form */}
        <section aria-labelledby="verify-form-title" style={{ marginBottom: '32px' }}>
          <h2 id="verify-form-title" style={{ fontSize: '18px', marginBottom: '16px', fontFamily: 'sans-serif' }}>
            Verify Certificate ID / पहचान संख्या सत्यापित करें
          </h2>
          <form onSubmit={handleVerifyId} style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              aria-label="Certificate Identifier"
              placeholder="e.g. SND-7K3Q9M2XW4PTH8RA"
              value={certId}
              onChange={(e) => setCertId(e.target.value)}
              style={{
                flex: 1,
                padding: '12px 16px',
                fontSize: '15px',
                border: `1px solid ${BORDER_SUBTLE}`,
                borderRadius: '4px',
                fontFamily: 'monospace'
              }}
            />
            <button
              type="submit"
              disabled={loading}
              style={{
                padding: '12px 24px',
                backgroundColor: ACCENT_PRIMARY,
                color: '#FFFFFF',
                fontWeight: 'bold',
                border: 'none',
                borderRadius: '4px',
                cursor: loading ? 'not-allowed' : 'pointer',
                fontFamily: 'sans-serif'
              }}
            >
              {loading ? 'Verifying...' : 'Verify'}
            </button>
          </form>
        </section>

        {/* Error Feedback */}
        {error && (
          <div role="alert" style={{ padding: '16px', background: '#FDF2F2', border: '1px solid #F8B4B4', color: '#A71D2A', borderRadius: '4px', marginBottom: '24px' }}>
            <strong>Verification Error:</strong> {error}
          </div>
        )}

        {/* Verification Verdict Display (Section 8.5) */}
        {result && (
          <section aria-labelledby="verdict-heading" style={{ borderTop: `1px solid ${BORDER_SUBTLE}`, paddingTop: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <span
                style={{
                  padding: '6px 14px',
                  borderRadius: '20px',
                  fontWeight: 'bold',
                  fontSize: '13px',
                  letterSpacing: '0.5px',
                  ...getVerdictBadgeStyle(result.verdict)
                }}
              >
                {result.verdict}
              </span>
              <span style={{ fontSize: '12px', color: '#7F7F82', fontFamily: 'sans-serif' }}>
                Pipeline latency: {result.durationMs}ms
              </span>
            </div>

            <p style={{ fontSize: '16px', fontWeight: '500', marginBottom: '24px', lineHeight: '1.4' }}>
              {result.summary}
            </p>

            {/* Certificate Details */}
            {result.certificate && (
              <div style={{ background: '#FBFBFA', border: `1px solid ${BORDER_SUBTLE}`, borderRadius: '6px', padding: '20px', marginBottom: '24px', fontFamily: 'sans-serif' }}>
                <h3 style={{ fontSize: '15px', margin: '0 0 12px 0', textTransform: 'uppercase', letterSpacing: '0.5px', color: '#575759' }}>
                  Attested Credential Record
                </h3>
                <dl style={{ margin: 0, display: 'grid', gridTemplateColumns: '140px 1fr', rowGap: '8px', fontSize: '14px' }}>
                  <dt style={{ color: '#575759' }}>Holder Name:</dt>
                  <dd style={{ margin: 0, fontWeight: 'bold' }}>{result.certificate.holderName}</dd>
                  <dt style={{ color: '#575759' }}>Degree & Major:</dt>
                  <dd style={{ margin: 0 }}>{result.certificate.title} in {result.certificate.programme}</dd>
                  <dt style={{ color: '#575759' }}>Issued On:</dt>
                  <dd style={{ margin: 0 }}>{result.certificate.issuedOn}</dd>
                  <dt style={{ color: '#575759' }}>Institution:</dt>
                  <dd style={{ margin: 0 }}>{result.certificate.institutionName || 'Demo Registered Institution'}</dd>
                </dl>
              </div>
            )}

            {/* Findings List (Explainable verification findings) */}
            <div style={{ fontFamily: 'sans-serif' }}>
              <h3 style={{ fontSize: '15px', margin: '0 0 12px 0', textTransform: 'uppercase', letterSpacing: '0.5px', color: '#575759' }}>
                Audit & Cryptographic Findings
              </h3>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {result.findings.map((f, i) => (
                  <li
                    key={i}
                    style={{
                      padding: '10px 14px',
                      background: f.outcome === 'pass' ? '#FAFCFA' : '#FFF9F9',
                      border: `1px solid ${f.outcome === 'pass' ? '#E1EFE1' : '#F6DCDC'}`,
                      borderRadius: '4px',
                      marginBottom: '8px',
                      fontSize: '13px',
                      display: 'flex',
                      justifyContent: 'space-between'
                    }}
                  >
                    <span><strong>{f.check}:</strong> {f.detail}</span>
                    <span style={{ fontWeight: 'bold', color: f.outcome === 'pass' ? '#0E6245' : '#A71D2A' }}>
                      {f.outcome.toUpperCase()}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
