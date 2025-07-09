import json

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from patients.models import Patient
from io import BytesIO
import qrcode
from django.core.files import File
import os
from auditlog.registry import auditlog
from auditlog.models import AuditlogHistoryField
from core.utils import generate_unified_qr  # Your centralized QR generator


class Bill(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]

    history = AuditlogHistoryField()

    # Relationships
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='bills'
    )

    # Financial Information
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Dates
    issued_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField(null=True, blank=True)
    paid_date = models.DateTimeField(null=True, blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Documents
    pdf_file = models.FileField(upload_to='bills/pdfs/', null=True, blank=True)
    qr_code = models.ImageField(upload_to='bills/qr_codes/', null=True, blank=True)

    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issued_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['issued_date']),
            models.Index(fields=['patient']),
        ]

    def __str__(self):
        return f"Bill #{self.id} - {self.patient.full_name} (${self.amount})"

    def get_absolute_url(self):
        return reverse('billing:bill_detail', kwargs={'pk': self.pk})

    def generate_qr_code(self):
        """Generate QR code linking to the patient's results portal"""
        portal_url = reverse(
            'patient_portal:results_portal',
            kwargs={'token': self.patient.qr_token}
        )
        full_url = f"{settings.SITE_URL}{portal_url}"

        qr_data = {
            "type": "patient_portal",
            "bill_id": self.id,
            "patient_id": self.patient.id,
            "url": full_url
        }

        # Generate QR code image
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
        self.qr_code.save(f'bill_{self.id}.png', File(buffer), save=False)

    def generate_pdf(self):
        """Generates PDF with embedded QR code (called by signals/utils)"""
        from billing.utils import render_bill_pdf  # Import locally to avoid circular imports

        # Ensure QR exists
        if not self.qr_code:
            self.generate_qr_code()
            self.save()

        # Generate PDF
        pdf_path = render_bill_pdf(self)
        if pdf_path:
            self.pdf_file.name = pdf_path
            self.save()

    def calculate_total(self):
        return self.amount + self.tax_amount - self.discount

    def is_overdue(self):
        return self.due_date and self.status == 'pending' and timezone.now() > self.due_date

    def save(self, *args, **kwargs):
        # Auto-set paid_date if status changes to 'paid'
        if self.status == 'paid' and not self.paid_date:
            self.paid_date = timezone.now()

        super().save(*args, **kwargs)

        # Generate documents if new bill
        if not self.pk or kwargs.get('force_generate', False):
            self.generate_qr_code()
            self.generate_pdf()
            super().save(update_fields=['qr_code', 'pdf_file'])


# Register with auditlog
auditlog.register(Bill)