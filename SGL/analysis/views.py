from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.urls import reverse_lazy
from .models import Analysis
from .forms import AnalysisForm


class AnalysisListView(ListView):
    model = Analysis
    template_name = 'analysis/analysis_list.html'
    context_object_name = 'analyses'
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().select_related('sample', 'analysis_type')


class AnalysisCreateView(CreateView):
    model = Analysis
    form_class = AnalysisForm
    template_name = 'analysis/analysis_form.html'
    success_url = reverse_lazy('analysis:list')


class AnalysisDetailView(DetailView):
    model = Analysis
    template_name = 'analysis/analysis_detail.html'
    context_object_name = 'analysis'


class AnalysisUpdateView(UpdateView):
    model = Analysis
    form_class = AnalysisForm
    template_name = 'analysis/analysis_form.html'
    context_object_name = 'analysis'

    def get_success_url(self):
        return reverse_lazy('analysis:detail', kwargs={'pk': self.object.pk})