from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import get_object_or_404
from users.models import User
from .models import Analysis, AnalysisType
from .forms import AnalysisForm
from samples.models import Sample

class AnalysisListView(ListView):
    model = Analysis
    template_name = 'analysis/analysis_list.html'
    context_object_name = 'analyses'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('sample', 'analysis_type')
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-created_at')

class AnalysisCreateView(CreateView):
    model = Analysis
    form_class = AnalysisForm
    template_name = 'analysis/analysis_form.html'
    success_url = reverse_lazy('analysis:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # Pass the user to the form
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Analyse créée avec succès!')
        return response

class AnalysisDetailView(DetailView):
    model = Analysis
    template_name = 'analysis/analysis_detail.html'
    context_object_name = 'analysis'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        analysis = self.get_object()
        context['results'] = analysis.result_set.all().order_by('-created_at')
        return context

class AnalysisUpdateView(UpdateView):
    model = Analysis
    form_class = AnalysisForm
    template_name = 'analysis/analysis_form.html'

    def get_success_url(self):
        return reverse_lazy('analysis:detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # Pass the user to the form
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Analyse mise à jour avec succès!')
        return response

def get_analysis_types(request):
    sample_id = request.GET.get('sample_id')
    try:
        sample = Sample.objects.get(id=sample_id)
        analysis_types = AnalysisType.objects.filter(
            sample_types=sample.sample_type
        ).values('id', 'name')
        return JsonResponse({
            'analysis_types': list(analysis_types)
        })
    except (ValueError, Sample.DoesNotExist):
        return JsonResponse({
            'analysis_types': []
        }, status=400)
def get_analysis_types(request):
    sample_id = request.GET.get('sample_id')
    try:
        sample = Sample.objects.get(id=sample_id)
        analysis_types = AnalysisType.objects.filter(
            sample_types=sample.sample_type
        ).values('id', 'name')
        return JsonResponse({
            'analysis_types': list(analysis_types)
        })
    except (ValueError, Sample.DoesNotExist):
        return JsonResponse({
            'analysis_types': []
        }, status=400)


def get_sample_type(request):
    return None