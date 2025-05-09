from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from patients.models import Patient
from samples.models import Sample
from analysis.models import Analysis
from results.models import Result
from django.db.models import Count


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
            'sample_status': {'labels': [], 'data': []}
        })

        try:
            context.update({
                'patient_count': Patient.objects.count(),
                'sample_count': Sample.objects.count(),
                'analysis_count': Analysis.objects.count(),
                'result_count': Result.objects.count(),
                'sample_status': self.get_sample_status()
            })
        except Exception as e:
            print(f"Error fetching dashboard data: {e}")

        return context

    def get_sample_status(self):
        if hasattr(Sample, 'status'):
            status_counts = Sample.objects.values('status').annotate(count=Count('status'))
            return {
                'labels': [s['status'] for s in status_counts],
                'data': [s['count'] for s in status_counts]
            }
        return {'labels': [], 'data': []}