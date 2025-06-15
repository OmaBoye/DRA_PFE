from django.db import models
from django.utils import timezone
from datetime import timedelta
import secrets
import qrcode
from io import BytesIO
from django.core.files import File
from django.core.validators import RegexValidator


class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    # Core Patient Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone_number = models.CharField(max_length=17)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    medical_history = models.TextField(blank=True)

    # QR Code System
    qr_code = models.ImageField(upload_to='qr_codes', blank=True)
    qr_token = models.CharField(max_length=64, blank=True)
    qr_token_expires = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        """
        Custom save method that:
        1. Generates QR token if missing
        2. Sets expiration date
        3. Generates QR code image for new patients
        """
        # Check if this is a new patient (before first save)
        is_new = not self.pk

        # Generate QR token if missing or expired
        if not self.qr_token or (self.qr_token_expires and self.qr_token_expires < timezone.now()):
            self.qr_token = secrets.token_urlsafe(32)
            self.qr_token_expires = timezone.now() + timedelta(days=30)

        # First save to ensure we have an ID for QR code generation
        super().save(*args, **kwargs)

        # Generate QR code image if new patient or QR code is missing
        if is_new or not self.qr_code:
            self.generate_qr_code()
            # Save again to store the QR code image
            super().save(update_fields=['qr_code'])

    def generate_qr_code(self):
        """Generate QR code image containing patient ID and token"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(f"PatientID:{self.id}:{self.qr_token}")
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        self.qr_code.save(f'qr_{self.id}.png', File(buffer), save=False)

    def is_qr_valid(self):
        """Check if the QR token is still valid"""
        if not self.qr_token_expires:
            return False
        return timezone.now() < self.qr_token_expires

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'