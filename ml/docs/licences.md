# Licence Ledger & Data Governance Register

**Project**: Sanad Machine Learning Subsystem (Academic Credential Authenticity Validator)  
**Date Established**: 1 November 2026  
**Governance Framework**: Strict academic integrity, non-commercial research attribution, and India Digital Personal Data Protection (DPDP) Act 2023 compliance.

---

## 1. Verified Dataset Catalogue

| Dataset | Canonical Source & Reference | Licence / Stated Terms | Commercial Status | Sanad Usage Scope | Notes & Constraints |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DocTamper** | CVPR 2023 (`github.com/qcf-568/DocTamper`) | Non-commercial research only (Gated; requires educational email author request) | **Strictly Non-Commercial** | Pretraining tamper localization (FPH, DTD) | Password-protected `.mdb` archives. Derived models inherit non-commercial limitation. |
| **SIDTD** | Scientific Data 2024 (`github.com/Oriolrt/SIDTD_Dataset`) | CC BY-SA 2.5 (arXiv text tagged CC BY-SA 4.0) | ShareAlike | Learning crop-and-replace, inpainting artifacts, print-recapture | Derivatives must share alike. Real ID reference set is private; genuine set uses synthetic MIDV-2020 faces. |
| **Find it again!** | ICDAR 2023 Competition | Not stated on portal | Restricted / Unconfirmed | Benchmark testing for manual forgeries | Small receipt set with rich edit bounding boxes. Private research use only until formal terms verified. |
| **AIForge-Doc** | 2026 Benchmark | Publicly released without registration (terms pending paper review) | Pending Review | Unseen zero-shot test set for AI-inpainted tampering | Modern threat evaluation. Baseline detectors typically show severe drop (0.509 - 0.563 AUC). |
| **Mozhi** | IIIT Hyderabad (Towards Deployable OCR Models for Indic Languages) | Not stated on portal; citation required | Academic / Citation required | Fine-tuning & evaluating Hindi text recognition on real word crops | 1.2M word crops across 13 Indian languages; ~100k Hindi words (80:10:10 split). |
| **IIIT-Synthetic-M-Hindi** | IIIT Hyderabad | "Can be used only for pre-training purposes", "All Rights Reserved" | **Restricted: Pre-training Only** | Pretraining Hindi OCR recognizer | 278,248 word crops across 97 Unicode fonts. Never used for final real-world accuracy claims. |
| **DocLayNet** | IBM Research / Hugging Face | CDLA-Permissive-1.0 | Permissive Open | Document layout analysis pretraining | 80,863 document pages with 11 layout categories. |
| **CORD** | Donut / NAVER Clova | CC BY-NC-SA 4.0 | Non-Commercial ShareAlike | Clean receipt OCR / field extraction | Multilingual receipts (Indonesian). |
| **SROIE** | ICDAR 2019 Task 2 & 3 | Academic Research Evaluation | Academic Non-Commercial | Key-field extraction pretraining | Scanned receipts. |

---

## 2. Unverified or Restricted Datasets

| Dataset / Source | Stated Claim | Verification Finding | Handling Decision |
| :--- | :--- | :--- | :--- |
| **RTM (Real Text Manipulation)** | DrLuo/RTM (14,250 text images) | Repository inaccessible / unreleased as of audit date | Excluded from active training; marked unverified. |
| **Roboflow "Certificate Forgery"** | CC BY 4.0 (3 classes) | No provenance, methodology, or subject consent documented | **Excluded from ground truth**. Do not use images depicting real persons. |
| **Synthetic Indic OCR (Saini et al.)** | arXiv 2205.02543 (90,000 images) | Languages unconfirmed, no direct download link or licence | Excluded until repository and language breakdown are confirmed. |

---

## 3. Layer 2: Real Consented Certificates Governance

- **Statutory Compliance**: Under India's Digital Personal Data Protection (DPDP) Act 2023 and 2025 Rules:
  - Personal data of Indian residents requires explicit, informed, revocable written consent.
  - Purpose limitation: strictly evaluation of document physical aging, stamp false alarms, and scanner quirks.
  - Zero Training Leakage: Layer 2 documents are never included in training sets or seen by model weights.
  - Storage: Stored encrypted at rest, isolated from version control, with an offline key and consent ledger.
  - Right to Erase: Upon consent withdrawal, all instances and derived evaluation caches are purged immediately.

---

## 4. Derived Model Licensing Implications

Any model trained or fine-tuned on DocTamper or IIIT-Synthetic-M-Hindi inherits non-commercial academic constraints. The Sanad repository maintains this explicit designation:
- Models utilizing DocTamper pretraining must be labelled `Sanad-DTD-Academic-NC`.
- Production deployments intended for enterprise or government use must rely exclusively on permissively licensed data and internal synthetic generation (Sanad-Cert).
