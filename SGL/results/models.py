from auditlog.models import AuditlogHistoryField
from django.contrib.auth import get_user_model
from django.db import models
from core.models import BaseModel
from samples.models import Sample
from patients.models import Patient
from auditlog.registry import auditlog
from simple_history.models import HistoricalRecords

User = get_user_model()
class Result(BaseModel):
    history = AuditlogHistoryField()

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
    ]
    qr_code = models.ImageField(upload_to='results/qr_codes/', blank=True, null=True)
    sample = models.OneToOneField(Sample, on_delete=models.CASCADE, related_name='result')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    test_date = models.DateTimeField()
    completed_date = models.DateTimeField(null=True, blank=True)
    verified_by = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    values = models.JSONField(default=dict)  # Stores test results in key-value pairs
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_results')

    def __str__(self):
        return f"Result for {self.sample}"

    @property
    def patient(self):
        return self.sample.patient

    class Meta:
        ordering = ['-test_date']

auditlog.register(Result)
HistoricalRecords.model = Result


def generate_qr_code(self):
    """Generate QR code that links back to patient's unified QR"""
    from core.utils import generate_unified_qr

    qr_data = {
        "type": "result",
        "id": self.id,
        "patient_id": self.analysis.sample.patient.id,
        "analysis_id": self.analysis.id,
        "status": self.status
    }

    qr_file = generate_unified_qr(qr_data, fill_color="#28a745")  # Green for results
    self.qr_code.save(f'result_{self.id}.png', qr_file, save=False)

    def save(self, *args, **kwargs):
        # Generate QR code if this is a new result
        if not self.pk and not self.qr_code:
            self.generate_qr_code()
        super().save(*args, **kwargs)