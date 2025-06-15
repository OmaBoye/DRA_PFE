# hl7_monitor/models.py
from django.db import models
from django.utils import timezone


class HL7Message(models.Model):
    MESSAGE_TYPES = (
        ('ADT^A01', 'Patient Admission'),
        ('ORM^O01', 'Lab Order'),
        ('ORU^R01', 'Lab Result'),
    )

    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    raw_message = models.TextField()
    direction = models.CharField(max_length=10, choices=[('IN', 'Inbound'), ('OUT', 'Outbound')])
    status = models.CharField(max_length=10, choices=[
        ('RECEIVED', 'Received'),
        ('PROCESSED', 'Processed'),
        ('ERROR', 'Error')
    ])
    timestamp = models.DateTimeField(default=timezone.now)
    processing_time = models.FloatField(null=True, blank=True)  # Seconds

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_message_type_display()} ({self.timestamp})"


class FHIRLog(models.Model):
    resource_type = models.CharField(max_length=50)
    action = models.CharField(max_length=10, choices=[('CREATE', 'Create'), ('SEARCH', 'Search')])
    status_code = models.IntegerField()
    request = models.TextField()
    response = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.resource_type} {self.action} ({self.status_code})"