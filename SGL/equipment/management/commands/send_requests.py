from django.core.management.base import BaseCommand
from analysis.models import Analysis
from equipment.models import EquipmentTestRequest, LaboratoryEquipment
from equipment.connectors import EquipmentConnector

class Command(BaseCommand):
    help = 'Send pending analyses to lab equipment'

    def handle(self, *args, **options):
        pending_analyses = Analysis.objects.filter(status='pending')
        equipment = LaboratoryEquipment.objects.filter(is_active=True).first()

        for analysis in pending_analyses:
            connector = EquipmentConnector(equipment.id)
            try:
                connector.send_request(analysis.id)
                EquipmentTestRequest.objects.create(
                    analysis=analysis,
                    equipment=equipment,
                    status='processed'
                )
                analysis.status = 'in_progress'
                analysis.save()
                self.stdout.write(f"Sent analysis {analysis.id} to {equipment.name}")
            except Exception as e:
                self.stderr.write(f"Failed for analysis {analysis.id}: {str(e)}")