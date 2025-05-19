# hl7_monitor/views.py
from django.views.generic import ListView, DetailView
from .models import HL7Message, FHIRLog
from django.db.models import Count, Q, Avg
from datetime import timedelta
from django.utils import timezone


class MessageDashboard(ListView):
    template_name = 'hl7_monitor/dashboard.html'
    model = HL7Message
    context_object_name = 'messages'
    paginate_by = 20

    def get_queryset(self):
        return HL7Message.objects.all().order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Stats for last 24 hours
        day_ago = timezone.now() - timedelta(days=1)
        context.update({
            'message_stats': HL7Message.objects.filter(
                timestamp__gte=day_ago
            ).values('message_type').annotate(
                count=Count('id'),
                avg_time=Avg('processing_time')
            ),
            'error_count': HL7Message.objects.filter(
                status='ERROR',
                timestamp__gte=day_ago
            ).count()
        })
        return context


class MessageDetail(DetailView):
    template_name = 'hl7_monitor/message_detail.html'
    model = HL7Message

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['raw_hl7'] = self.object.raw_message.replace('\r', '<br>')
        return context


class FHIRLogView(ListView):
    template_name = 'hl7_monitor/fhir_logs.html'
    model = FHIRLog
    paginate_by = 20
    ordering = ['-timestamp']