from django.core.management.base import BaseCommand
from equipment.models import EquipmentTestRequest, EquipmentResult, LaboratoryEquipment
from equipment.connectors import EquipmentConnector
from results.models import Result


class Command(BaseCommand):
    help = 'Check equipment for new results'

    def handle(self, *args, **options):
        # Get first active equipment or exit if none exists
        equipment = LaboratoryEquipment.objects.filter(is_active=True).first()

        if not equipment:
            self.stderr.write("Error: No active lab equipment configured!")
            return  # Exit gracefully

        connector = EquipmentConnector(equipment.id)

        try:
            results = connector.poll_results()
            if not results:
                self.stdout.write("No new results found")
                return

            for raw_result in results:
                try:
                    test_request = EquipmentTestRequest.objects.get(
                        analysis__sample__barcode=raw_result['sample_id']
                    )
                    EquipmentResult.objects.create(
                        test_request=test_request,
                        raw_data=raw_result
                    )
                    # Auto-create Result record
                    Result.objects.create(
                        sample=test_request.analysis.sample,
                        values=raw_result['values'],
                        status='completed'
                    )
                    self.stdout.write(f"Processed result for {raw_result['sample_id']}")
                except EquipmentTestRequest.DoesNotExist:
                    self.stderr.write(f"No test request found for sample {raw_result['sample_id']}")
                except Exception as e:
                    self.stderr.write(f"Error processing result: {str(e)}")

        except Exception as e:
            self.stderr.write(f"Polling failed: {str(e)}")