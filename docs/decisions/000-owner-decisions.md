# Owner Decisions Record

Date: 2026-10-31
Status: Initial Baseline Assumptions Recorded (Awaiting explicit owner overrides if desired)

Pursuant to Section 15 of the Master Build Prompt, this document records the formal operating assumptions and answers to the ten mandatory owner questions to establish the Phase 0 baseline.

---

### 1. Product Name and Domain
- **Decision / Assumption**: The working name is **Sanad** (as designated in Section 1). Public documentation and UI copy will use "Sanad (Authenticity Validator for Academia)" as a prototype designation.
- **Domain**: Canonical domain is set to `localhost` in local development, with environment-configurable canonical host `sanad.local` / `sanad.ac.in` prepared for production deployment.

### 2. Primary Goal
- **Decision / Assumption**: Dual focus on **Jury Demonstration (Smart India Hackathon SIH25029)** and **Academic College Submission**, with pilot-grade architecture. All modules are designed so that real pilot readiness is maintained without architectural re-work.

### 3. Timeline and Capacity
- **Decision / Assumption**: Lead engineer working through structured phases (Phase 0 to Phase 7) according to the phased build plan in Section 14, targeting full test-verified completion with automated regression coverage.

### 4. Pilot Institution Agreements
- **Decision / Assumption**: No real institution's name or identity is claimed without written consent. The system initiates with two clearly labelled synthetic demo institutions:
  1. `Demo Institute of Technology (sample, not a real institution)`
  2. `Jharkhand State Technical University (sample demo institution)`
  Both utilize synthetic templates and verified deterministic mock records.

### 5. External Anchoring
- **Decision / Assumption**:
  1. Primary Anchor: `LogAnchor` (local SHA-256 transparency log with inclusion proof generation).
  2. Public Anchor: `EvmAnchor` targeting a public EVM testnet (e.g. Sepolia or Polygon Amoy). Zero mainnet fees will be spent. Testnet receipts are explicitly labeled as such in the interface.

### 6. Key Custody
- **Decision / Assumption**: Phase 1 through Phase 6 ship with `ServerSigner` (institution private keys encrypted at rest with AES-GCM-256 using an environment-managed Key Encryption Key `SANAD_KEK`). Phase 7 delivers `BrowserSigner` / offline CLI signing capability. The security limitation of `ServerSigner` is explicitly stated in README and documentation.

### 7. National Depository / Government Integrations
- **Decision / Assumption**: No active production API access is assumed for DigiLocker, NAD, or APAAR. In accordance with Section 2, all such external bodies are built behind typed interface adapters and marked strictly as `NOT CONNECTED` in the user interface and API metadata.

### 8. Repository License
- **Decision / Assumption**: Apache-2.0 or MIT License (permissible open source suitable for educational and government technical evaluations), documented in `docs/licences.md`.

### 9. Hosting Budget
- **Decision / Assumption**: Zero dollar / local development budget using standard Docker Compose and Caddy. Suitable for local jury demonstration on a single laptop or low-cost Linux VPS.

### 10. Language Scope
- **Decision / Assumption**: Version 1 ships with complete bilingual support for **English** and **Hindi (हिंदी)** for all public-facing verification flows and error messages.
