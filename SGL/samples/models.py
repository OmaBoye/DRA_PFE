from datetime import timezone, timedelta

from django.db import models
from core.models import BaseModel
from patients.models import Patient


class SampleQuerySet(models.QuerySet):
    def last_30_days(self):
        return self.filter(
            collection_date__gte=timezone.now() - timedelta(days=30)
        )

    def last_90_days(self):
        return self.filter(
            collection_date__gte=timezone.now() - timedelta(days=90)
        )


class SampleType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    processing_days = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name

class Sample(BaseModel):
    objects = SampleQuerySet.as_manager()

    STATUS_CHOICES = [
        ('collected', 'Collected'),
        ('received', 'Received in Lab'),
        ('processing', 'Processing'),
        ('analyzed', 'Analyzed'),
        ('reported', 'Reported'),
        ('archived', 'Archived'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='samples')
    sample_type = models.ForeignKey(SampleType, on_delete=models.PROTECT)
    collection_date = models.DateTimeField()
    received_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='collected')
    notes = models.TextField(blank=True)
    barcode = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.patient} - {self.sample_type} ({self.status})"

    class Meta:
        ordering = ['-collection_date']


