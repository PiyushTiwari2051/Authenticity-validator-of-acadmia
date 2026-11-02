# Dependency Licences and Intellectual Property Audit

Date: 2026-10-31
Compliance Standard: Strict permissive open-source licensing; zero non-commercial or viral copyleft in core distribution.

---

## 1. Backend Runtimes & Libraries

| Dependency | Purpose | Licence | Justification |
|------------|---------|---------|---------------|
| **FastAPI** | High-performance async ASGI REST API | MIT | Standard, well-documented, automatic OpenAPI schema generation. |
| **Pydantic v2** | Strict data validation & typing | MIT | Industry standard for contract enforcement and request parsing. |
| **Uvicorn** | ASGI web server implementation | BSD-3-Clause | Lightweight, fast event loop integration. |
| **SQLAlchemy 2.0** | Type-annotated async ORM & SQL generator | MIT | Enterprise-grade relational mapping, query safety, connection pooling. |
| **Asyncpg** | High-performance PostgreSQL async driver | Apache-2.0 | Proven PostgreSQL driver with high throughput. |
| **Alembic** | Relational schema migrations | MIT | Standard relational migration engine for SQLAlchemy. |
| **Redis-py** | Async Redis client for caching & queues | MIT | Native, reliable Redis driver. |
| **PyNaCl (libsodium)** | Ed25519 signing and verification | Apache-2.0 | Hardened cryptographic library binding libsodium. |
| **canonicaljson / jcs** | RFC 8785 JSON canonicalization | Apache-2.0 / BSD | Conforms to strict IETF RFC 8785 standard. |
| **Argon2-cffi** | Password hashing conforming to RFC 9106 | MIT | Winner of the Password Hashing Competition; memory-hard against GPU attacks. |
| **PyPPM / PyPDF / ReportLab** | A4 Certificate generation & PDF inspection | BSD / Apache / AGPL (substitutable with WeasyPrint/ReportLab BSD) | Clean programmatic generation of print-ready certificates. |
| **Pillow (PIL)** | Image rasterization & preprocessing | HPND / MIT-like | Robust image handling with `MAX_IMAGE_PIXELS` protection. |
| **OpenCV-Python-headless** | Computer vision & forensic heuristics | Apache-2.0 | Standard CV framework without desktop GUI baggage. |
| **PyTesseract** | Wrapper for Tesseract OCR | Apache-2.0 | Open-source measurable OCR engine. |
| **Structlog** | Structured JSON logging | Apache-2.0 / MIT | Non-blocking structured logging with contextual fields. |

---

## 2. Frontend Runtimes & Libraries

| Dependency | Purpose | Licence | Justification |
|------------|---------|---------|---------------|
| **Next.js 14/15** | React framework with Server Components | MIT | Fast server-side rendering for mobile verifiers, zero initial JS bloat. |
| **React & React-DOM** | UI component architecture | MIT | Standard declarative UI rendering. |
| **Lucide-React** | Accessible, clean UI iconography | ISC | Crisp, accessible iconography without decorative excess. |
| **HTML5-QRCode** | Mobile camera barcode scanning fallback | Apache-2.0 | Robust in-browser camera QR scanning fallback. |

---

## 3. Infrastructure & Services

| Service | Component | Licence | Deployment Model |
|---------|-----------|---------|------------------|
| **PostgreSQL 16** | Core relational database | PostgreSQL License (MIT-style) | Containerized service |
| **Redis 7** | Cache, rate limiting, task queues | BSD-3-Clause | Containerized service |
| **MinIO** | S3-compatible object storage | AGPLv3 (Server runtime) | Separate service container accessed exclusively via standard S3 REST API. |
| **Caddy** | Reverse proxy with automated TLS | Apache-2.0 | Front-line proxy and TLS termination. |

---

## 4. IP & Model Restrictions
- **No Non-Commercial Datasets / Models**: No pretrained checkpoints with restrictive non-commercial licenses (e.g. CC-BY-NC) are incorporated into the production build.
- **Evaluation Synthetic Data**: All evaluation datasets are synthetically generated from demo templates created within this project.
