from django.core.management.base import BaseCommand
from analysis.models import Analysis
from results.models import Result
import random
from django.utils import timezone
from django.db import transaction


class Command(BaseCommand):
    help = 'Generate timezone-aware mock lab results'

    def handle(self, *args, **options):
        # Safe test profiles with clinical ranges
        TEST_PROFILES = {
            'CBC': {
                'WBC': (4.0, 11.0),  # x10³/μL
                'RBC': (4.2, 6.1),  # x10⁶/μL
                'HGB': (12.0, 18.0),  # g/dL
                'HCT': (37, 54),  # %
                'PLT': (150, 450),  # x10³/μL
            },
            'BMP': {
                'GLU': (70, 100),  # mg/dL
                'CA': (8.5, 10.2),  # mg/dL
                'NA': (135, 145),  # mmol/L
                'K': (3.5, 5.2),  # mmol/L
                'CL': (98, 107),  # mmol/L
                'CO2': (23, 29),  # mmol/L
            }
        }

        with transaction.atomic():  # Ensures all changes succeed or fail together
            pending_analyses = Analysis.objects.filter(
                status='pending',
                sample__isnull=False
            ).select_related('sample', 'analysis_type')

            if not pending_analyses.exists():
                self.stdout.write(self.style.WARNING('No pending analyses found'))
                return

            for analysis in pending_analyses:
                try:
                    # Get current time with timezone
                    now = timezone.now()

                    # Determine test type safely
                    test_type = 'CBC'  # Default
                    if analysis.analysis_type and analysis.analysis_type.code:
                        test_type = analysis.analysis_type.code.split('-')[0].strip().upper()
                        if test_type not in TEST_PROFILES:
                            test_type = 'CBC'

                    # Generate realistic values with 10% chance of abnormal
                    mock_values = {}
                    for param, (low, high) in TEST_PROFILES[test_type].items():
                        if random.random() < 0.1:  # 10% chance of abnormal
                            mock_values[param] = round(random.uniform(
                                low * 0.7 if random.random() < 0.5 else high * 1.3,
                                low * 0.9 if random.random() < 0.5 else high * 1.1
                            ), 2)
                        else:
                            mock_values[param] = round(random.uniform(low, high), 2)

                    # Create/update result with timezone-aware datetime
                    Result.objects.update_or_create(
                        sample=analysis.sample,
                        defaults={
                            'values': mock_values,
                            'status': 'completed',
                            'test_date': now,
                            'notes': f"Auto-generated {test_type} results"
                        }
                    )

                    # Update analysis
                    analysis.status = 'completed'
                    analysis.completed_at = now
                    analysis.save()

                    self.stdout.write(
                        self.style.SUCCESS(f'Created {test_type} results for {analysis.sample.barcode}')
                    )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Failed for {analysis.id}: {str(e)}')
                    )
                    continue