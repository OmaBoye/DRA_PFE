from django.db import models
from django.urls import reverse
from core.models import BaseModel
from patients.models import Patient
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta
import qrcode
from io import BytesIO
from django.core.files import File
import secrets
import logging

logger = logging.getLogger(__name__)


class SampleQuerySet(models.QuerySet):
    def last_30_days(self):
        return self.filter(
            collection_date__gte=timezone.now() - timedelta(days=30))

    def last_90_days(self):
        return self.filter(
            collection_date__gte=timezone.now() - timedelta(days=90))

    def by_status(self, status):
        return self.filter(status=status)

    def for_batch(self):
        return self.filter(status='collected')


class SampleType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    processing_days = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['name']
        verbose_name = "Sample Type"

    def __str__(self):
        return self.name


class Sample(BaseModel):
    STATUS_CHOICES = [
        ('collected', 'Collected'),
        ('received', 'Received in Lab'),
        ('processing', 'Processing'),
        ('analyzed', 'Analyzed'),
        ('reported', 'Reported'),
        ('archived', 'Archived'),
        ('rejected', 'Rejected'),
    ]

    REJECTION_REASONS = [
        ('hemolyzed', 'Hemolyzed'),
        ('insufficient', 'Insufficient Volume'),
        ('contaminated', 'Contaminated'),
    ]

    objects = SampleQuerySet.as_manager()

    # Core Fields
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='samples')
    sample_type = models.ManyToManyField(SampleType)
    collection_date = models.DateTimeField()
    received_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='collected')
    rejection_reason = models.CharField(max_length=20, choices=REJECTION_REASONS, blank=True, null=True)
    rejection_notes = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True)
    barcode = models.CharField(max_length=50, unique=True)
    current_technician = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_samples'
    )

    # QR Code System
    qr_code = models.ImageField(upload_to='qr_codes/samples/', blank=True, null=True)
    qr_token = models.CharField(max_length=64, blank=True)
    qr_token_expires = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-collection_date']
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['status']),
            models.Index(fields=['collection_date']),
        ]

    def __str__(self):
        return f"{self.patient} - {self.get_sample_types_display()} ({self.status})"

    def save(self, *args, **kwargs):
        """Handle QR code generation and status transitions"""
        if self.status == 'received' and not self.received_date:
            self.received_date = timezone.now()

        # Generate QR token if missing or expired
        if not self.qr_token or (self.qr_token_expires and self.qr_token_expires < timezone.now()):
            self.qr_token = secrets.token_urlsafe(32)
            self.qr_token_expires = timezone.now() + timedelta(days=30)

        super().save(*args, **kwargs)

        # Generate QR code after initial save when we have an ID
        if not self.qr_code:
            self.generate_qr_code()
            super().save(update_fields=['qr_code'])

    def generate_qr_code(self):
        """Generate QR code that links back to patient's unified QR"""
        from core.utils import generate_unified_qr

        qr_data = {
            "type": "sample",
            "id": self.id,
            "patient_id": self.patient.id,
            "barcode": self.barcode,
            "collection_date": self.collection_date.strftime('%Y-%m-%d')
        }

        qr_file = generate_unified_qr(qr_data)
        self.qr_code.save(f'sample_{self.id}.png', qr_file, save=False)

    def get_sample_types_display(self):
        return ", ".join([st.name for st in self.sample_type.all()])

    def get_absolute_url(self):
        return reverse('sample-detail', kwargs={'pk': self.pk})

    @property
    def processing_time(self):
        if self.received_date and self.collection_date:
            return (self.received_date - self.collection_date).days
        return None

    def is_qr_valid(self):
        return self.qr_token_expires and timezone.now() < self.qr_token_expires


class CustodyLog(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name='custody_logs')
    from_technician = models.ForeignKey('users.User', on_delete=models.PROTECT, related_name='transfers_out')
    to_technician = models.ForeignKey('users.User', on_delete=models.PROTECT, related_name='transfers_in')
    transferred_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-transferred_at']


class Batch(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey('users.User', on_delete=models.PROTECT, related_name='sample_batches')
    created_at = models.DateTimeField(auto_now_add=True)
    samples = models.ManyToManyField(Sample, related_name='batches')
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    batch_qr_code = models.ImageField(upload_to='qr_codes/batches/', blank=True, null=True)

    def generate_batch_qr(self):
        """Generate QR code containing all sample IDs in batch"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=6,
                border=4,
            )

            sample_ids = "\n".join([s.barcode for s in self.samples.all()])
            qr_data = f"""
            BATCH_ID:{self.id}
            CREATED:{self.created_at.date()}
            SAMPLES:
            {sample_ids}
            """

            qr.add_data(qr_data.strip())
            qr.make(fit=True)

            img = qr.make_image(fill_color="#3a7bd5", back_color="white")  # Blue color
            buffer = BytesIO()
            img.save(buffer, format="PNG")

            self.batch_qr_code.save(
                f'batch_{self.id}.png',
                File(buffer),
                save=False
            )
            self.save()
        except Exception as e:
            logger.error(f"Failed to generate batch QR: {str(e)}")


class Bill(models.Model):
    sample = models.OneToOneField(Sample, on_delete=models.CASCADE, related_name='bill')
    issued_date = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    pdf_file = models.FileField(upload_to='bills/', blank=True)