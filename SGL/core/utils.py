# core/utils.py
import qrcode
import json
import secrets
from io import BytesIO
from datetime import timedelta
from django.core.files import File
from django.utils import timezone
from django.core.exceptions import ValidationError


# ========================
# QR CODE SYSTEM
# ========================

def generate_unified_qr(data_dict, fill_color="black", back_color="white", size=10):
    """
    Generate standardized QR codes for all apps.

    Args:
        data_dict (dict): Structured data to encode (must include 'type' and 'id')
        fill_color (str): Hex color for QR foreground
        back_color (str): Hex color for QR background
        size (int): Pixel size per module

    Returns:
        File: Django File object with PNG QR code
    """
    # Validate input format
    if not isinstance(data_dict, dict) or 'type' not in data_dict or 'id' not in data_dict:
        raise ValidationError("QR data must be a dict with 'type' and 'id' fields")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=4,
    )

    # Add metadata and standardized timestamp
    full_data = {
        **data_dict,
        "system": "SGL_LIMS",  # Identify your system
        "generated_at": timezone.now().isoformat()
    }

    qr.add_data(json.dumps(full_data))
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return File(buffer)


def generate_secure_token(expiry_days=30):
    """Generate tokens for QR validation"""
    return {
        "token": secrets.token_urlsafe(32),
        "expires": timezone.now() + timedelta(days=expiry_days)
    }


def validate_qr_token(token, expiry_date):
    """Check if a QR token is still valid"""
    return token and expiry_date and timezone.now() < expiry_date


# ========================
# BARCODE SYSTEM
# ========================

def validate_barcode(code):
    """Ensure barcodes follow lab standards"""
    if not code.startswith(('SMP-', 'ANL-', 'PT-', 'BL-')):
        raise ValidationError("Barcode must start with SMP-, ANL-, PT-, or BL-")
    if len(code) != 10:
        raise ValidationError("Barcode must be 10 characters long")
    return True


def generate_standard_barcode(prefix="SMP"):
    """
    Generate standardized barcodes with checksum.
    Format: PREFIX-XXXXC (where C is a checksum digit)
    """
    import random
    digits = ''.join(str(random.randint(0, 9)) for _ in range(4))
    checksum = str(sum(int(d) for d in digits) % 10)
    return f"{prefix}-{digits}{checksum}"


# ========================
# TYPE-SPECIFIC QR HELPERS
# ========================

def generate_patient_qr(patient):
    """Standardized QR for Patient model"""
    return generate_unified_qr({
        "type": "patient",
        "id": patient.id,
        "name": patient.full_name,
        "dob": patient.date_of_birth.strftime('%Y-%m-%d'),
        **generate_secure_token()
    }, fill_color="#4e73df")  # Blue


def generate_bill_qr(bill):
    """Standardized QR for Bill model"""
    return generate_unified_qr({
        "type": "bill",
        "id": bill.id,
        "patient_id": bill.patient.id,
        "amount": str(bill.amount),
        "status": bill.status
    }, fill_color="#1cc88a")  # Green


def generate_result_qr(result):
    """Standardized QR for Result model"""
    return generate_unified_qr({
        "type": "result",
        "id": result.id,
        "patient_id": result.sample.patient.id,
        "test_code": result.analysis.analysis_type.code,
        "status": result.status
    }, fill_color="#f6c23e")  # Yellow


# ========================
# SCANNING UTILITIES
# ========================

def decode_unified_qr(image_file):
    """
    Decode QR images into standardized data.
    Returns:
        dict: Decoded data if valid
        None: If invalid
    """
    from pyzbar.pyzbar import decode
    from PIL import Image

    try:
        img = Image.open(image_file)
        decoded = decode(img)
        if decoded:
            data = json.loads(decoded[0].data.decode('utf-8'))

            # Basic validation
            if not all(k in data for k in ('type', 'id', 'system')):
                return None

            if data['system'] != "SGL_LIMS":
                return None

            return data
    except Exception:
        return None