# analytics/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from samples.models import Sample
from analytics.models import TurnaroundTime


@receiver(post_save, sender=Sample)
def calculate_turnaround_time(sender, instance, **kwargs):
    if instance.status == 'reported' and instance.collection_date and instance.received_date:
        from datetime import timedelta
        receipt_time = (instance.received_date - instance.collection_date).total_seconds() / 3600
        result_time = (instance.result.completed_at - instance.received_date).total_seconds() / 3600

        TurnaroundTime.objects.update_or_create(
            sample=instance,
            defaults={
                'collection_to_receipt_hours': receipt_time,
                'receipt_to_result_hours': result_time
            }
        )