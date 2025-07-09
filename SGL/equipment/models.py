from django.db import models
from analysis.models import Analysis

class LaboratoryEquipment(models.Model):
    name = models.CharField(max_length=100)
    model = models.CharField(max_length=50)
    ip_address = models.CharField(max_length=15)
    protocol = models.CharField(max_length=20, choices=[('HL7', 'HL7'), ('REST', 'REST'), ('TCP', 'TCP')])
    is_active = models.BooleanField(default=True)

class EquipmentTestRequest(models.Model):
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE)
    equipment = models.ForeignKey(LaboratoryEquipment, on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('processed', 'Processed')])

class EquipmentResult(models.Model):
    test_request = models.OneToOneField(EquipmentTestRequest, on_delete=models.CASCADE)
    raw_data = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)
    is_parsed = models.BooleanField(default=False)