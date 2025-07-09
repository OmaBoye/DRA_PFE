# analytics/models.py
from django.db import models
from django.utils import timezone
from samples.models import Sample
from results.models import Result
from datetime import timedelta
from samples.models import Sample
from analysis.models import Analysis



class LabPerformanceQuerySet(models.QuerySet):
    def last_30_days(self):
        return self.filter(
            date__gte=timezone.now().date() - timedelta(days=30)
        ).order_by('date')

    def last_7_days(self):
        return self.filter(
            date__gte=timezone.now().date() - timedelta(days=7)
        ).order_by('date')

class LabPerformance(models.Model):
    date = models.DateField(unique=True)
    samples_processed = models.IntegerField(default=0)
    avg_processing_time = models.FloatField(help_text="In hours")
    critical_results = models.IntegerField(default=0)

    @classmethod
    def update_daily_metrics(cls):
        today = timezone.now().date()
        samples = Sample.objects.filter(collection_date__date=today)
        results = Result.objects.filter(test_date__date=today)

        cls.objects.update_or_create(
            date=today,
            defaults={
                'samples_processed': samples.count(),
                'avg_processing_time': cls._calculate_avg_time(samples),
                'critical_results': results.filter(status='critical').count()
            }
        )

    @staticmethod
    def _calculate_avg_time(samples):
        from django.db.models import Avg, F
        return samples.annotate(
            processing_time=F('result__test_date') - F('collection_date')
        ).aggregate(
            avg_time=Avg('processing_time')
        )['avg_time'] or 0

class TurnaroundTime(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE)
    collection_to_receipt_hours = models.FloatField()  # Time from collection to lab receipt
    receipt_to_result_hours = models.FloatField()      # Time from receipt to result
    total_hours = models.FloatField()

    class Meta:
        indexes = [models.Index(fields=['total_hours'])]

    def save(self, *args, **kwargs):
        self.total_hours = self.collection_to_receipt_hours + self.receipt_to_result_hours
        super().save(*args, **kwargs)