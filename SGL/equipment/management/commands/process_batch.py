from django.core.management.base import BaseCommand
from django.utils import timezone
from analysis.models import BatchAnalysis
from samples.models import Batch

class Command(BaseCommand):
    help = 'Process batch analyses'

    def handle(self, *args, **options):
        pending_batches = BatchAnalysis.objects.filter(status='pending')

        for batch in pending_batches:
            try:
                batch.status = 'in_progress'
                batch.started_at = timezone.now()
                batch.save()

                # Process all samples in the batch
                for sample in batch.batch.samples.all():
                    # Your analysis processing logic here
                    pass

                batch.status = 'completed'
                batch.completed_at = timezone.now()
                batch.save()

            except Exception as e:
                batch.status = 'failed'
                batch.save()
                self.stderr.write(f"Failed to process batch {batch.id}: {str(e)}")