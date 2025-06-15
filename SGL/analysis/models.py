from django.db import models
from core.models import BaseModel
from samples.models import SampleType


class AnalysisType(models.Model):
    CATEGORY_CHOICES = [
        ('blood', 'Blood Analysis'),
        ('urine', 'Urine Analysis'),
        ('tissue', 'Tissue Analysis'),
        ('molecular', 'Molecular Analysis'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='blood')
    description = models.TextField(blank=True)
    sample_types = models.ManyToManyField(SampleType, related_name='analysis_types')
    default_parameters = models.JSONField(default=list)

    # Blood-specific fields
    is_blood_panel = models.BooleanField(default=False)
    blood_panels = models.JSONField(default=list, blank=True, null=True)

    def __str__(self):
        return f"{self.get_category_display()}: {self.name}"


class Analysis(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    PRIORITY_CHOICES = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('stat', 'Stat'),
    ]

    BLOOD_PANELS = [
        ('cbc', 'Complete Blood Count'),
        ('cmp', 'Comprehensive Metabolic Panel'),
        ('lipid', 'Lipid Panel'),
        ('thyroid', 'Thyroid Panel'),
        ('coagulation', 'Coagulation Panel'),
    ]

    sample = models.ForeignKey('samples.Sample', on_delete=models.CASCADE, related_name='analyses')
    analysis_type = models.ForeignKey(AnalysisType, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='routine')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    technician = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='created_analyses'
    )
    selected_panels = models.JSONField(default=list, blank=True)  # Store selected blood panels

    def __str__(self):
        return f"{self.analysis_type} for {self.sample}"

    class Meta:
        verbose_name_plural = 'analyses'
        ordering = ['-created_at']