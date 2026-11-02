# Datasheet for Sanad-Cert and Pretraining Corpus

Following the standard *Datasheets for Datasets* framework (Gebru et al., 2021).

## 1. Motivation

- **Why was the dataset created?**
  No publicly verifiable dataset of real Indian academic credentials (degrees, marksheets, grade cards) exists with documented, pixel-level manipulation ground truth due to legitimate privacy laws (India DPDP Act 2023) and copyright protections. Existing document tampering benchmarks (e.g. DocTamper, Find it again!) focus predominantly on receipts, forms, or general identity cards. Sanad-Cert was created to provide a statistically rigorous, leak-free, reproducible training and evaluation dataset explicitly designed for academic credential forgery detection.

- **Who created the dataset?**
  The Sanad Engineering & Research Team (Academic Authenticity Validator initiative, Smart Education theme).

- **Who funded the creation of the dataset?**
  Academic and student research initiative (with institutional affiliations noted in project documentation).

---

## 2. Composition

- **What do the instances that comprise the dataset represent?**
  Each instance is a document image representing an academic credential:
  - **Layer 1 (Public Real Pretraining Data)**: Document crops and receipts from verified public sources (Mozhi, DocTamper, SIDTD, DocLayNet) used strictly for generic feature learning and Indic OCR.
  - **Layer 2 (Consented Genuine Documents)**: Real academic scans from adult students (18+) who provided signed, revocable consent. Kept strictly isolated in a private locked test partition to benchmark scanner, fold, and stamp false-alarm rates.
  - **Layer 3 (Sanad-Cert Synthetic & Tampered)**: Procedurally rendered credentials spanning 8 distinct template families across fictitious demo institutions, paired with deterministic arithmetic, genuine digital signatures, QR codes, and 10 systematic tampering recipes (T1 to T10) with exact pixel-level masks.

- **How many instances are there in total?**
  - Target Phase D3 Synthetic Generation: 600 genuine synthetic base documents, producing 1,800 tampered variants (minimum 100 per recipe T1–T10) across 8 template families.
  - Physical captures: 120 printed and recaptured across varying lighting, skew, and camera/scanner devices.
  - Layer 2 real set: Up to 60 consented documents held out exclusively as a test set.

- **Does the dataset contain all possible instances or is it a sample?**
  It is a controlled representative sample reflecting standard Indian university document layouts, grading scales, and tampering vectors.

- **What data does each instance consist of?**
  - Document image (`.png` / `.jpg`).
  - Binary manipulation ground-truth mask (`.png` where 255 = manipulated pixel, 0 = authentic).
  - Metadata record in `ml/data/MANIFEST.csv` specifying template ID, group ID, recipe ID, split allocation, capture parameters, and cryptographic SHA-256 hash.

- **Is any information missing or unrepresented?**
  Real student identities and genuine university crests are deliberately omitted to preserve ethical standards and legal compliance.

---

## 3. Collection / Synthesis Process

- **How was the data acquired or generated?**
  1. *Generation*: Built using Sanad's internal issuing pipeline using ReportLab/Pillow with procedural security rosettes, guilloche borders, and synthetic institutional seals.
  2. *Integrity*: Every document's marksheet arithmetic (subject totals, percentages, CGPA conversions) is calculated deterministically to prevent accidental forensic anomalies.
  3. *Tampering Execution*:
     - **T1**: Manual photo-editing simulation.
     - **T2**: Scripted font-matched text replacement.
     - **T3**: Inpainting removal and re-rendering.
     - **T4**: Deep learning inpainting (AIForge-Doc style).
     - **T5**: Intrapage copy-move of seals and signatures.
     - **T6**: Cross-document splicing.
     - **T7**: Font-mismatched text editing.
     - **T8**: Semantically consistent mark manipulation (recalculated totals).
     - **T9**: Print-and-recapture degradation.
     - **T10**: Complete regeneration / typesetting (zero pixel-level anomaly; tests registry discrepancy).

- **Who was involved in the data collection process?**
  Sanad core research engineers.

---

## 4. Preprocessing, Cleaning, and Labeling

- All images are normalized to 300 DPI rasterization equivalent with standardized coordinate mapping.
- Exact difference masks are computed via pixel-delta verification between original and tampered buffers.
- Group hashing prevents near-duplicate contamination across train/val/test splits.

---

## 5. Uses

- **What are the intended uses?**
  Evaluating document tampering detection models (such as Document Tampering Detector / DTD, CAT-Net, TruFor), measuring Hindi/English OCR performance under degradation, and benchmarking multi-modal forensic fusion pipelines.

- **What tasks should this dataset NOT be used for?**
  - Training or creating automated tools for forging real university credentials.
  - Claiming a single universal accuracy number for arbitrary unseen real-world documents without stating the exact test conditions and dataset provenance.

---

## 6. Distribution & Maintenance

- **How is the dataset distributed?**
  Code recipes, generators, manifest files, and hashes are maintained within the repository.
  Raw personal consented documents remain encrypted in offline storage and are never distributed.
- **Licensing**:
  Code and synthetic generators: Open academic use.
  External pretraining weights and datasets: Subject to their respective upstream licenses as recorded in `docs/licences.md`.
