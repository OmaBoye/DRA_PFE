import os
from io import BytesIO
from django.template.loader import render_to_string
from django.urls import reverse
from xhtml2pdf import pisa
from django.conf import settings
from django.core.files.base import ContentFile
import qrcode
from django.core.files import File
import logging

logger = logging.getLogger(__name__)


def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources. This is specifically needed for media files.
    """
    # Handle media files
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    # Handle static files
    elif uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
    else:
        # Handle absolute URIs (e.g., http://example.com)
        return uri

    # Make sure the file exists
    if not os.path.isfile(path):
        logger.warning(f"Media file not found: {path}")
        return uri

    return path


def generate_bill_pdf(bill):
    """Generate PDF file for a bill and save it to the model"""
    # Ensure QR code exists
    if not bill.qr_code:
        generate_qr_code(bill)
        bill.save()

    context = {
        'bill': bill,
        'logo_path': os.path.join(settings.STATIC_ROOT, 'img/logo.png'),
        'MEDIA_URL': settings.MEDIA_URL,
        'SITE_NAME': getattr(settings, 'SITE_NAME', ''),
        'SITE_ADDRESS': getattr(settings, 'SITE_ADDRESS', ''),
        'SITE_PHONE': getattr(settings, 'SITE_PHONE', ''),
        'SITE_EMAIL': getattr(settings, 'SITE_EMAIL', '')
    }

    html = render_to_string('billing/bill_pdf_template.html', context)
    result = BytesIO()

    pdf = pisa.pisaDocument(
        BytesIO(html.encode("UTF-8")),
        result,
        link_callback=link_callback
    )

    if not pdf.err:
        pdf_dir = os.path.join(settings.MEDIA_ROOT, 'bills/pdfs')
        os.makedirs(pdf_dir, exist_ok=True)

        file_path = os.path.join(pdf_dir, f'bill_{bill.id}.pdf')

        # Save the PDF to disk
        with open(file_path, 'wb') as f:
            f.write(result.getvalue())

        # Save to model
        if bill.pdf_file:
            bill.pdf_file.delete(save=False)

        bill.pdf_file.save(f'bills/pdfs/bill_{bill.id}.pdf', ContentFile(result.getvalue()))
        return True

    logger.error(f"PDF generation error: {pdf.err}")
    return False


def generate_qr_code(bill):
    """Generate QR code for a bill"""
    try:
        portal_url = reverse(
            'patient_portal:results_portal',
            kwargs={'token': bill.patient.qr_token}
        )
        full_url = f"{settings.SITE_URL}{portal_url}"

        qr_data = {
            "type": "patient_portal",
            "bill_id": bill.id,
            "patient_id": bill.patient.id,
            "url": full_url
        }

        # Generate QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(str(qr_data))
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Delete old QR if exists
        if bill.qr_code:
            bill.qr_code.delete(save=False)

        # Save new QR code
        bill.qr_code.save(
            f'bills/qr_codes/bill_{bill.id}.png',
            File(buffer),
            save=False
        )
        return True
    except Exception as e:
        logger.error(f"Error generating QR code for bill {bill.id}: {str(e)}")
        return False