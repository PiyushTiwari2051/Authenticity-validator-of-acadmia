# Authenticity Validator for Academia

Academic certificate authenticity verification platform.

- Real-time forensic analysis (ELA, OCR, cryptographic signature)
- Brutalist UI/UX — black, white, one light blue
- Ed25519 institutional keypair verification
- English + Hindi bilingual
- WCAG 2.2 AA accessible

## Run locally

```bash
node standalone_server.js
```

Open http://localhost:3000

## Stack

- Node.js (zero dependencies server)
- Python 3.11 + RapidOCR + OpenCV (forensic engine)
- Vanilla HTML/CSS/JS (brutalist design system)
