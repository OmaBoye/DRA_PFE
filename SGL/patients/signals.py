# patients/signals.py
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from celery.exceptions import RetryError
from .models import Patient
from integrations.tasks import sync_patient_to_ehr, delete_patient_from_ehr

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Patient)
def handle_patient_sync(sender, instance, created, **kwargs):
    """
    Sync patient data with external EHR systems after save.
    Handles both creation and updates.
    """
    if not settings.INTEGRATIONS_ENABLED:  # Configurable flag
        return

    try:
        if created:
            # New patient - full sync
            logger.info(f"Queueing initial EHR sync for new patient {instance.id}")
            sync_patient_to_ehr.delay(instance.id)
        else:
            # Existing patient - incremental update
            if _patient_has_changes(instance):
                logger.info(f"Queueing update for modified patient {instance.id}")
                sync_patient_to_ehr.delay(instance.id)
    except Exception as e:
        logger.error(f"Failed to queue EHR sync for patient {instance.id}: {str(e)}")
        if settings.DEBUG:
            raise  # Only raise in development


@receiver(post_delete, sender=Patient)
def handle_patient_deletion(sender, instance, **kwargs):
    """
    Remove patient from external EHR systems when deleted locally.
    """
    if not settings.INTEGRATIONS_ENABLED:
        return

    try:
        logger.info(f"Queueing EHR deletion for patient {instance.id}")
        delete_patient_from_ehr.delay(instance.id)
    except Exception as e:
        logger.error(f"Failed to queue EHR deletion for patient {instance.id}: {str(e)}")
        if settings.DEBUG:
            raise


def _patient_has_changes(instance):
    """
    Check if critical patient fields have changed to avoid unnecessary syncs.
    """
    if not instance.pk:
        return False

    try:
        old = Patient.objects.get(pk=instance.pk)
        return (
                old.first_name != instance.first_name or
                old.last_name != instance.last_name or
                old.date_of_birth != instance.date_of_birth or
                old.gender != instance.gender
        )
    except Patient.DoesNotExist:
        return False


# Connect signals only if integrations are enabled
if settings.INTEGRATIONS_ENABLED:
    post_save.connect(handle_patient_sync, sender=Patient)
    post_delete.connect(handle_patient_deletion, sender=Patient)
else:
    logger.info("Patient signals disabled - INTEGRATIONS_ENABLED=False")