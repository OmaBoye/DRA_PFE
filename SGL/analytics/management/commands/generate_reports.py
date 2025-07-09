# analytics/manaent/commands/generate_reports.py
from django.core.management.base import BaseCommand
from analytics.models import LabPerformance
from datetime import timedelta
from django.db import models
from django.utils import timezone


class Command(BaseCommand):
    help = 'Generates daily performance reports'

    def handle(self, *args, **options):
        # Update today's metrics
        LabPerformance.update_daily_metrics()

        # Weekly summary (last 7 days)
        weekly_data = LabPerformance.objects.filter(
            date__gte=timezone.now().date() - timedelta(days=7)
        ).values('date').annotate(
            total_samples=models.Sum('samples_processed'),
            avg_time=models.Avg('avg_processing_time')
        )

        self.stdout.write(self.style.SUCCESS(f'Generated {weekly_data.count()} daily records'))