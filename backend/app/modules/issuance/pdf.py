"""Certificate PDF Generator.
Produces high-quality A4 document with institution credentials and high-density QR code.
"""

import io
import qrcode
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm


def generate_certificate_pdf(
    certificate_id: str,
    institution_name: str,
    holder_name: str,
    degree_title: str,
    programme: str,
    division: str,
    issued_on: str,
    verification_url: str,
) -> bytes:
    """Generate high-resolution A4 academic certificate PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CertTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        alignment=1,  # Center
        textColor=colors.HexColor("#1C355E")
    )
    inst_style = ParagraphStyle(
        "CertInst",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        alignment=1,
        textColor=colors.HexColor("#2C2C2E")
    )
    body_style = ParagraphStyle(
        "CertBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        alignment=1,
        textColor=colors.HexColor("#333333")
    )
    name_style = ParagraphStyle(
        "CertName",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        alignment=1,
        textColor=colors.HexColor("#18181A")
    )

    story = []

    story.append(Spacer(1, 20))
    story.append(Paragraph(institution_name.upper(), inst_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("OFFICIAL ATTESTATION OF DEGREE", title_style))
    story.append(Spacer(1, 25))

    story.append(Paragraph("This is to certify that", body_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph(holder_name, name_style))
    story.append(Spacer(1, 15))

    cert_text = (
        f"has successfully completed all academic requirements and examinations for the degree of "
        f"<b>{degree_title}</b> in <b>{programme}</b>, and is awarded the same in the "
        f"<b>{division}</b> division on {issued_on}."
    )
    story.append(Paragraph(cert_text, body_style))
    story.append(Spacer(1, 40))

    # Generate QR Code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#18181A", back_color="#FFFFFF")

    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    reportlab_img = Image(qr_buffer, width=1.5 * inch, height=1.5 * inch)

    # Footer layout table
    footer_text = Paragraph(
        f"<b>Certificate ID:</b> {certificate_id}<br/>"
        f"<b>Verify at:</b> {verification_url}<br/>"
        "<i>Digitally signed under Sanad W3C VC 2.0 cryptosuite. Scan QR to verify.</i>",
        ParagraphStyle("Foot", parent=styles["Normal"], fontSize=9, leading=12, textColor=colors.HexColor("#555555"))
    )

    footer_table = Table(
        [[footer_text, reportlab_img]],
        colWidths=[4.8 * inch, 1.8 * inch]
    )
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))

    story.append(footer_table)

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
