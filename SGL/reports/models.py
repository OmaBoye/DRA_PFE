from django.db import models
from core.models import BaseModel
from results.models import Result
from patients.models import Patient

class Report(BaseModel):
    result = models.OneToOneField(Result, on_delete=models.CASCADE, related_name='report')
    generated_by = models.CharField(max_length=100)
    approved_by = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    template_name = models.CharField(max_length=100, default='default')

    def __str__(self):
        return f"Report for {self.result.sample}"

    @property
    def patient(self):
        return self.result.patient

    class Meta:
        ordering = ['-created_at']