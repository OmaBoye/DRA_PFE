# analytics/views.py
from django.views.generic import TemplateView
from django_pandas.io import read_frame
from analytics.models import TurnaroundTime
from django.db.models import Avg
from analytics import models
from analytics.models import LabPerformance
import plotly.express as px
from django.shortcuts import render
from samples.models import Sample


class TurnaroundTimeReport(TemplateView):
    template_name = 'analytics/turnaround.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = LabPerformance.objects.last_30_days()

        # Create Plotly figure
        df = read_frame(qs)
        fig = px.line(
            df,
            x='date',
            y='avg_processing_time',
            title='Temps Moyen de Traitement (30 jours)',
            labels={'avg_processing_time': 'Heures'}
        )

        context['chart'] = fig.to_html()
        return context


def sample_throughput(request):
    samples = Sample.objects.last_90_days().annotate(
        day=models.functions.TruncDay('collection_date')
    ).values('day').annotate(
        count=models.Count('id'),
        type=models.F('sample_type__name')
    )

    fig = px.bar(
        samples,
        x='day',
        y='count',
        color='type',
        title='Échantillons par Type (90 jours)'
    )

    return render(request, 'analytics/throughput.html', {
        'chart': fig.to_html()
    })


class AnalyticsDashboard(TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = TurnaroundTime.objects.all().values(
            'sample__patient__first_name',
            'total_hours'
        )

        # Plotly chart
        fig = px.bar(
            x=[d['sample__patient__first_name'] for d in data],
            y=[d['total_hours'] for d in data],
            title="Turnaround Time by Patient"
        )
        context['chart'] = fig.to_html()

        # Stats
        context['avg_time'] = TurnaroundTime.objects.aggregate(
            avg_total=Avg('total_hours'),
            avg_receipt=Avg('collection_to_receipt_hours'),
            avg_processing=Avg('receipt_to_result_hours')
        )
        return context