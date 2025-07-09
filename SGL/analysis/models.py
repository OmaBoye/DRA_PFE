from django.db import models
from core.models import BaseModel
from samples.models import SampleType, Batch
from auditlog.registry import auditlog
from auditlog.models import AuditlogHistoryField
from django.core.exceptions import ValidationError
import json
from django.urls import reverse
from django.conf import settings
from billing.models import Bill  # Import Bill model for foreign key


class AnalysisType(models.Model):
    """Defines different types of laboratory analyses that can be performed."""
    CATEGORY_CHOICES = [
        ('blood', 'Blood Analysis'),
        ('urine', 'Urine Analysis'),
        ('tissue', 'Tissue Analysis'),
        ('molecular', 'Molecular Analysis'),
        ('microbiology', 'Microbiology'),
    ]

    history = AuditlogHistoryField()

    # Basic Information
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='blood')
    description = models.TextField(blank=True)

    # Sample Requirements
    sample_types = models.ManyToManyField(SampleType, related_name='analysis_types')
    minimum_sample_volume = models.CharField(max_length=50, blank=True)
    sample_storage_conditions = models.CharField(max_length=100, blank=True)

    # Testing Configuration
    default_parameters = models.JSONField(default=list)
    turnaround_time = models.PositiveIntegerField(
        default=24,
        help_text="Standard turnaround time in hours"
    )
    is_auto_verifiable = models.BooleanField(
        default=False,
        help_text="Can results be auto-verified without manual review?"
    )

    # Blood-specific fields
    is_blood_panel = models.BooleanField(default=False)
    blood_panels = models.JSONField(default=list, blank=True, null=True)

    # Pricing and Billing
    test_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    insurance_codes = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Analysis Type'
        verbose_name_plural = 'Analysis Types'

    def __str__(self):
        return f"{self.get_category_display()}: {self.name}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_test_code()
        super().save(*args, **kwargs)

    def generate_test_code(self):
        """Auto-generates a test code if none provided"""
        prefix = self.category[:3].upper()
        return f"{prefix}-{self.name[:4].upper()}"


class Analysis(BaseModel):
    """Tracks individual lab test analyses performed on samples."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
        ('cancelled', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('routine', 'Routine (7-10 hours)'),
        ('urgent', 'Urgent (4 hours)'),
        ('stat', 'STAT (<1 hour)'),
    ]

    BLOOD_PANELS = [
        ('cbc', 'Complete Blood Count'),
        ('cmp', 'Comprehensive Metabolic Panel'),
        ('lipid', 'Lipid Panel'),
        ('thyroid', 'Thyroid Panel'),
        ('coagulation', 'Coagulation Panel'),
    ]

    history = AuditlogHistoryField()

    # Relationships
    sample = models.ForeignKey(
        'samples.Sample',
        on_delete=models.CASCADE,
        related_name='analyses'
    )
    analysis_type = models.ForeignKey(
        AnalysisType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='analyses'
    )
    bill = models.ForeignKey(
        'billing.Bill',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analyses'
    )

    # Status Tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='routine'
    )

    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    # Personnel
    technician = models.CharField(max_length=100, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_analyses'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_analyses'
    )

    # Test Details
    notes = models.TextField(blank=True)
    selected_panels = models.JSONField(default=list, blank=True)
    instrument_used = models.CharField(max_length=100, blank=True)
    qc_status = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name_plural = 'Analyses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['sample']),
            models.Index(fields=['analysis_type']),
            models.Index(fields=['bill']),  # New index for billing
        ]

    def __str__(self):
        return f"Analysis #{self.id} for {self.sample} ({self.get_status_display()})"

    def clean(self):
        """Validate model before saving"""
        super().clean()

        # 1. Sample Type Validation
        if self.sample and self.analysis_type:
            allowed_types = self.analysis_type.sample_types.all()
            if allowed_types and not self.sample.sample_type.filter(id__in=allowed_types).exists():
                raise ValidationError(
                    f"Sample type '{self.sample.get_sample_types_display()}' "
                    f"is invalid for {self.analysis_type.name}. "
                    f"Allowed: {', '.join([t.name for t in allowed_types])}"
                )

        # 2. Status Logic Validation
        if self.completed_at and not self.started_at:
            raise ValidationError("Cannot have completion date without start date")

        if self.status == 'verified' and not self.verified_by:
            raise ValidationError("Must specify who verified this analysis")

    def get_absolute_url(self):
        return reverse('analysis:detail', kwargs={'pk': self.pk})

    @property
    def is_complete(self):
        return self.status in ['completed', 'verified']

    @property
    def is_billed(self):
        return self.bill is not None

    @property
    def turnaround_time(self):
        """Calculate actual turnaround time in hours"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() / 3600
        return None


class AnalysisResult(models.Model):
    analysis = models.OneToOneField(
        Analysis,
        on_delete=models.CASCADE,
        related_name='result'
    )
    raw_data = models.JSONField(help_text="Original equipment output")
    formatted_data = models.JSONField(help_text="Human-readable formatted results")
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    pdf_report = models.FileField(
        upload_to='reports/%Y/%m/',
        null=True,
        blank=True
    )
    is_auto_generated = models.BooleanField(default=False)

    # User references with proper related_names
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_results'
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='modified_results'
    )

    # Denormalized fields for cross-app access
    patient_id = models.IntegerField(blank=True, null=True)  # From Analysis→Sample→Patient
    test_code = models.CharField(max_length=20, blank=True)  # From AnalysisType

    class Meta:
        indexes = [
            models.Index(fields=['patient_id']),
            models.Index(fields=['test_code']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Result for {self.analysis}"

    def save(self, *args, **kwargs):
        if not self.pk:  # First save
            self.patient_id = self.analysis.sample.patient_id
            self.test_code = self.analysis.analysis_type.code
        super().save(*args, **kwargs)

class BatchAnalysis(models.Model):
    analyses = models.ManyToManyField('Analysis', related_name='batches')
    analysis_type = models.ForeignKey(AnalysisType, on_delete=models.PROTECT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='analysis_batches')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='pending')

    def __str__(self):
        return f"Batch {self.id} - {self.analysis_type.name}"

# Register models with auditlog
auditlog.register(AnalysisType)
auditlog.register(Analysis)
auditlog.register(AnalysisResult)