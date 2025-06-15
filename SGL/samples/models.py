from datetime import timezone, timedelta
from django.db import models
from django.urls import reverse
from core.models import BaseModel
from patients.models import Patient
from django.core.validators import MinValueValidator

class SampleQuerySet(models.QuerySet):
    def last_30_days(self):
        """Return samples collected in the last 30 days."""
        return self.filter(
            collection_date__gte=timezone.now() - timedelta(days=30)
        )

    def last_90_days(self):
        """Return samples collected in the last 90 days."""
        return self.filter(
            collection_date__gte=timezone.now() - timedelta(days=90)
        )

    def by_status(self, status):
        """Filter samples by status."""
        return self.filter(status=status)

class SampleType(models.Model):
    """Model representing different types of samples that can be collected."""
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The name of the sample type (e.g., Blood, Urine)"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the sample type"
    )
    processing_days = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Number of days typically needed to process this sample type"
    )

    class Meta:
        ordering = ['name']
        verbose_name = "Sample Type"
        verbose_name_plural = "Sample Types"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('sample-type-detail', kwargs={'pk': self.pk})

class Sample(BaseModel):
    STATUS_CHOICES = [
        ('collected', 'Collected'),
        ('received', 'Received in Lab'),
        ('processing', 'Processing'),
        ('analyzed', 'Analyzed'),
        ('reported', 'Reported'),
        ('archived', 'Archived'),
    ]

    paid = models.BooleanField(default=False)
    objects = SampleQuerySet.as_manager()

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='samples',
        help_text="The patient from whom this sample was collected"
    )
    sample_type = models.ManyToManyField(
        SampleType,
        help_text="The type of sample collected"
    )
    collection_date = models.DateTimeField(
        help_text="Date and time when the sample was collected"
    )
    received_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time when the sample was received in the lab"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='collected',
        help_text="Current status of the sample in the workflow"
    )
    notes = models.TextField(
        blank=True,
        help_text="Any additional notes about the sample"
    )
    barcode = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique barcode identifier for the sample"
    )

    class Meta:
        ordering = ['-collection_date']
        verbose_name = "Sample"
        verbose_name_plural = "Samples"
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['status']),
            models.Index(fields=['collection_date']),
        ]

    def __str__(self):
        return f"{self.patient} - {self.sample_type} ({self.status})"

    def get_sample_types_display(self):
        return ", ".join([st.name for st in self.sample_type.all()])

    def get_absolute_url(self):
        return reverse('sample-detail', kwargs={'pk': self.pk})

    @property
    def processing_time(self):
        """Calculate processing time if sample has been received."""
        if self.received_date and self.collection_date:
            return (self.received_date - self.collection_date).days
        return None

    def save(self, *args, **kwargs):
        """Custom save method to handle status transitions."""
        if self.status == 'received' and not self.received_date:
            self.received_date = timezone.now()
        super().save(*args, **kwargs)

class Bill(models.Model):
    sample = models.OneToOneField(Sample, on_delete=models.CASCADE, related_name='bill')
    issued_date = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    pdf_file = models.FileField(upload_to='bills/', blank=True)

    def __str__(self):
        return f"Bill for {self.sample.barcode}"

@property
def sample_types_display(self):
    return ", ".join([st.name for st in self.sample_type.all()])