# views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from hl7_monitor.models import HL7Message
from django.views.generic import TemplateView

from analysis.models import Analysis
from patients.models import Patient
from results.models import Result
from samples.models import Sample


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Initialize counts with 0
        context.update({
            'patient_count': 0,
            'sample_count': 0,
            'analysis_count': 0,
            'result_count': 0,
            'sample_status': {'labels': [], 'data': []},
            'throughput_data': {'labels': [], 'data': []}
        })

        try:
            # Existing counts
            context.update({
                'patient_count': Patient.objects.count(),
                'sample_count': Sample.objects.count(),
                'analysis_count': Analysis.objects.count(),
                'result_count': Result.objects.count(),
                'sample_status': self.get_sample_status(),
                'throughput_data': self.get_throughput_data()
            })
        except Exception as e:
            print(f"Error fetching dashboard data: {e}")

        return context

    def get_throughput_data(self):
        # Get samples from last 30 days grouped by day
        thirty_days_ago = timezone.now() - timedelta(days=30)

        throughput = (
            Sample.objects
            .filter(collection_date__gte=thirty_days_ago)
            .extra({'day': "date(collection_date)"})
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )

        # Create complete date range with zeros for missing days
        date_range = [
                         (timezone.now() - timedelta(days=x)).date()
                         for x in range(30)
                     ][::-1]  # Reverse to get chronological order

        throughput_dict = {item['day']: item['count'] for item in throughput}

        return {
            'labels': [d.strftime('%Y-%m-%d') for d in date_range],
            'data': [throughput_dict.get(d, 0) for d in date_range]
        }

    def get_sample_status(self):
        if hasattr(Sample, 'status'):
            status_counts = Sample.objects.values('status').annotate(count=Count('status'))
            return {
                'labels': [s['status'] for s in status_counts],
                'data': [s['count'] for s in status_counts]
            }
        return {'labels': [], 'data': []}