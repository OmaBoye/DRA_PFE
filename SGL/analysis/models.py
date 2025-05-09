from django.db import models
from core.models import BaseModel
from samples.models import SampleType

class AnalysisType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    sample_types = models.ManyToManyField(SampleType, related_name='analysis_types')
    default_parameters = models.JSONField(default=list)  # [{"name": "param1", "unit": "mg/dL"}, ...]

    def __str__(self):
        return self.name

class Analysis(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    sample = models.ForeignKey('samples.Sample', on_delete=models.CASCADE, related_name='analyses')
    analysis_type = models.ForeignKey(AnalysisType, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    technician = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.analysis_type} for {self.sample}"

    class Meta:
        verbose_name_plural = 'analyses'
        ordering = ['-created_at']