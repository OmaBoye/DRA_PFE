import json
import secrets
import logging
from io import BytesIO
from datetime import timedelta, date

from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.core.files import File
from django.core.validators import RegexValidator
import qrcode

from core.utils import generate_unified_qr

logger = logging.getLogger(__name__)

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
    qr_code = models.ImageField(upload_to='patient_qr_codes/', blank=True)
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

    @property
    def age(self):
        return (date.today() - self.date_of_birth).days // 365

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'

    def save(self, *args, **kwargs):
        """Override save to handle QR code generation"""
        is_new = not self.pk

        # Generate QR token if missing or expired
        if not self.qr_token or self.is_qr_expired():
            self.qr_token = secrets.token_urlsafe(32)
            self.qr_token_expires = timezone.now() + timedelta(days=30)

        super().save(*args, **kwargs)

        # Generate QR code if new patient or missing
        if is_new or not self.qr_code:
            self.generate_qr_code()
            super().save(update_fields=['qr_code', 'qr_token', 'qr_token_expires'])

    def is_qr_expired(self):
        """Check if QR token has expired"""
        self.qr_token_expires = timezone.now() + timedelta(days=365)

    def generate_qr_code(self):
        try:
            portal_url = reverse('patient_portal:results_portal', kwargs={'token': self.qr_token})
            full_url = f"{settings.SITE_URL}{portal_url}"
            print(f"DEBUG - Generated URL: {full_url}")  # Add this line

            qr_data = {
                "type": "patient",
                "id": self.id,
                "token": self.qr_token,
                "name": self.full_name,
                "dob": self.date_of_birth.strftime('%Y-%m-%d'),
                "url": full_url
            }

            # Generate QR image
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")

            # Delete old QR if exists
            if self.qr_code:
                self.qr_code.delete(save=False)

            # Save new QR code
            self.qr_code.save(f'patient_{self.id}.png', File(buffer), save=False)
            return True

        except Exception as e:
            logger.error(f"Failed to generate QR code for patient {self.id}: {str(e)}")
            return False

    def generate_bill(self):
        """Generate a bill for this patient with QR code"""
        from billing.models import Bill
        try:
            bill, created = Bill.objects.get_or_create(
                patient=self,
                defaults={
                    'amount': 100.00,  # Default amount
                    'status': 'pending'
                }
            )

            if created or not bill.qr_code:
                qr_data = {
                    "type": "patient_bill",
                    "patient_id": self.id,
                    "bill_id": bill.id,
                    "timestamp": timezone.now().isoformat(),
                    "portal_url": reverse('patient_portal:results_portal', kwargs={'token': self.qr_token})
                }

                qr_file = generate_unified_qr(qr_data, fill_color="#007bff")
                bill.qr_code.save(f'bill_{bill.id}.png', qr_file, save=True)

            return bill

        except Exception as e:
            logger.error(f"Failed to generate bill for patient {self.id}: {str(e)}")
            raise

    @property
    def analyses(self):
        """Get all analyses for this patient"""
        from analysis.models import Analysis
        return Analysis.objects.filter(sample__patient=self)

    def get_available_results(self):
        """Get completed results for this patient"""
        from results.models import Result
        return Result.objects.filter(
            sample__patient=self,
            status='completed'
        ).select_related('sample', 'sample__analysis_type')