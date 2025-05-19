from django.core.management.base import BaseCommand
from django.utils import timezone
from patients.models import Patient
from results.models import Result
from datetime import timedelta

class Command(BaseCommand):
    help = "Deletes records older than X years"

    def add_arguments(self, parser):
        parser.add_argument('--years', type=int, default=5, help='Years to keep')

    def handle(self, *args, **options):
        years = options['years']
        cutoff_date = timezone.now() - timedelta(days=365 * years)

        # Delete old patients (adjust query as needed)
        deleted_patients, _ = Patient.objects.filter(created_at__lt=cutoff_date).delete()
        deleted_results, _ = Result.objects.filter(created_at__lt=cutoff_date).delete()

        self.stdout.write(f"Deleted {deleted_patients} patients and {deleted_results} results older than {years} years")