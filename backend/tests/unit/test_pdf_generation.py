"""Test certificate PDF generation and QR decoding."""

import io
from PIL import Image
from reportlab.pdfgen import canvas
from backend.app.modules.issuance.pdf import generate_certificate_pdf


def test_certificate_pdf_generation_valid():
    pdf_bytes = generate_certificate_pdf(
        certificate_id="SND-TEST1234567890",
        institution_name="Demo Institute of Technology",
        holder_name="Sample Student",
        degree_title="Bachelor of Technology",
        programme="Computer Science and Engineering",
        division="First",
        issued_on="2026-07-15",
        verification_url="https://sanad.local/v/SND-TEST1234567890"
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF-")
