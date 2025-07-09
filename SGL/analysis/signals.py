# analysis/signals.py
import logging

from django.core.files.base import ContentFile
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from SGL import settings
from equipment.models import EquipmentResult, EquipmentTestRequest
from analysis.models import AnalysisResult
from analysis.utils import format_equipment_data
from analysis.services import generate_result_pdf

logger = logging.getLogger(__name__)

@receiver(post_save, sender=EquipmentResult)
def process_equipment_result(sender, instance, created, **kwargs):
    """Signal handler for processing equipment results"""
    if not created:
        return

    try:
        # 1. Format the raw equipment data
        formatted_data = format_equipment_data(instance.raw_data)

        # 2. Create the analysis result record
        result = AnalysisResult.objects.create(
            analysis=instance.test_request.analysis,
            raw_data=instance.raw_data,
            formatted_data=formatted_data,
            is_auto_generated=True,
            is_approved=instance.test_request.analysis.analysis_type.is_auto_verifiable
        )

        # 3. Generate PDF report
        generate_result_pdf(result)  # This should trigger the mock

        logger.info(f"Created result for analysis {instance.test_request.analysis.id}")

    except Exception as e:
        logger.error(f"Failed to process result: {str(e)}")
        raise


@receiver(post_save, sender=EquipmentTestRequest)
def generate_mock_results(sender, instance, created, **kwargs):
    if not created or not settings.DEBUG:
        return

    from services.mock_result_service import MockResultGenerator
    values = MockResultGenerator.generate_mock_values(instance.analysis.analysis_type.code)

    # Create EquipmentResult
    EquipmentResult.objects.create(
        test_request=instance,
        raw_data={'values': values}
    )

    # Generate PDF report
    pdf_content = MockResultGenerator.generate_pdf(
        instance.analysis.sample.barcode,
        values
    )

    # Save to AnalysisResult
    AnalysisResult.objects.update_or_create(
        analysis=instance.analysis,
        defaults={
            'raw_data': {'values': values},
            'formatted_data': MockResultGenerator.format_for_display(values),
            'pdf_report': ContentFile(pdf_content, f"result_{instance.id}.pdf")
        }
    )