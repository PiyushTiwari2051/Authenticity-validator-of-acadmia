# Competitive Differentiation Matrix

Date: 2026-11-01
Scope: Comparative analysis of 5 existing credential verification products vs. Sanad's intentional design and architectural departures.

---

### 1. DigiLocker (Government of India)
- **What it does**: A central government digital wallet providing citizen access to authenticated electronic documents issued by partner departments and examination boards.
- **What Sanad does differently on purpose**: DigiLocker requires an Aadhaar login, OTP round-trips, and citizen pre-registration before any verification can occur. Sanad allows anyone (employers, university admissions) to verify a certificate instantly in under 1.5 seconds via a public QR code or ID lookup with zero login, zero biometric collection, and deterministic cryptographic proof.

### 2. OpenCerts (GovTech Singapore)
- **What it does**: An open-source standard for issuing and verifying educational credentials anchored on the Ethereum blockchain.
- **What Sanad does differently on purpose**: OpenCerts requires users to upload raw `.opencert` JSON files (unfamiliar to everyday HR teams who receive paper or scanned PDFs). Furthermore, OpenCerts blurs legacy physical certificates by rejecting them completely. Sanad provides the non-negotiable **Road B** advisory pipeline for legacy paper scans, along with a standalone offline Merkle inclusion proof verification tool.

### 3. DocuSign / e-Signature Platforms
- **What it does**: General-purpose commercial electronic signature workflow platform for agreements, NDAs, and corporate signing.
- **What Sanad does differently on purpose**: DocuSign treats signatures as a business-to-business contract workflow with audit certificates stapled to the end of PDFs, often behind heavy enterprise paywalls. Sanad is purpose-built for academia: minimal data envelopes, unguessable Base32 IDs, student-governed selective disclosure, and public transparency logs.

### 4. Blockcerts (MIT Media Lab / Learning Machine)
- **What it does**: Open standard for academic credentials on Bitcoin and Ethereum blockchains.
- **What Sanad does differently on purpose**: Blockcerts relies heavily on blockchain transaction fees (gas) and native mobile apps. Sanad uses an append-only transparency log (`LogAnchor`) with optional EVM testnet anchoring, ensuring zero ongoing transaction costs for universities, and runs natively in mobile browsers with zero app installation.

### 5. Certif-ID / Commercial Blockchain Credential Suites
- **What it does**: SaaS platforms marketing "100% tamper-proof blockchain degrees" with promotional marketing dashboards and generic AI scorecards.
- **What Sanad does differently on purpose**: Sanad explicitly avoids dishonest marketing claims. We openly state in the interface and documentation that a digital signature proves *who signed* and *that nothing changed*, not that the registrar was honest. Sanad rejects fake percentage scores (e.g. "98.6% Authentic") and provides human-explained verification findings.
