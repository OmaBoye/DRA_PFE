from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from analysis.models import Analysis
from results.models import Result
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Analysis)
def validate_analysis_status_change(sender, instance, **kwargs):
    """
    Validate analysis status transitions before saving.
    Prevents invalid status changes like reverting from 'completed' to 'pending'.
    """
    if not instance.pk:  # New instance, no validation needed
        return

    try:
        original = Analysis.objects.get(pk=instance.pk)
        if original.status == 'completed' and instance.status != 'completed':
            raise ValidationError("Cannot modify status from 'completed'")
    except Analysis.DoesNotExist:
        pass


@receiver(post_save, sender=Analysis)
def handle_analysis_status_change(sender, instance, created, **kwargs):
    """
    Main signal handler for analysis workflow automation:
    - Creates pending result when sent to instrument
    - Auto-verifies results for simple tests
    """
    if instance.status == 'in_progress':
        handle_in_progress_analysis(instance)
    elif instance.status == 'completed':
        handle_completed_analysis(instance)


def handle_in_progress_analysis(analysis):
    """Create a pending result when analysis is sent to instrument"""
    if hasattr(analysis.sample, 'result'):
        logger.warning(f"Sample {analysis.sample.id} already has a result")
        return

    try:
        Result.objects.create(
            sample=analysis.sample,
            analysis_type=analysis.analysis_type,
            status='pending',
            test_date=analysis.started_at,
            technician=analysis.technician,
            values={}  # To be populated by instrument
        )
        logger.info(f"Created pending result for analysis {analysis.id}")
    except Exception as e:
        logger.error(f"Failed creating result for analysis {analysis.id}: {str(e)}")


def handle_completed_analysis(analysis):
    """Auto-verify results that don't require manual review"""
    try:
        result = analysis.sample.result
        if result.status == 'pending' and analysis.analysis_type.is_auto_verifiable:
            result.status = 'completed'
            result.completed_date = analysis.completed_at
            result.save()
            logger.info(f"Auto-verified result {result.id}")
    except Exception as e:
        logger.error(f"Failed processing completed analysis {analysis.id}: {str(e)}")