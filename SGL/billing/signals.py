from django.db.models.signals import post_save
from django.dispatch import receiver
from patients.models import Patient
from .models import Bill

@receiver(post_save, sender=Patient)
def create_patient_bill(sender, instance, created, **kwargs):
    if created:
        instance.generate_bill()


@receiver(post_save, sender=Bill)
def generate_bill_qr_code(sender, instance, created, **kwargs):
    if created and not instance.qr_code:
        instance.generate_qr_code()