from django.db import models
from core.models import BaseModel
from samples.models import Sample
from patients.models import Patient

class Result(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
    ]

    sample = models.OneToOneField(Sample, on_delete=models.CASCADE, related_name='result')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    test_date = models.DateTimeField()
    completed_date = models.DateTimeField(null=True, blank=True)
    verified_by = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    values = models.JSONField(default=dict)  # Stores test results in key-value pairs

    def __str__(self):
        return f"Result for {self.sample}"

    @property
    def patient(self):
        return self.sample.patient

    class Meta:
        ordering = ['-test_date']