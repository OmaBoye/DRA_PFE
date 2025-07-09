from django.http import HttpResponse
from django.utils import timezone
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.urls import reverse_lazy, reverse
from django.contrib import messages

from samples.models import Batch
from .models import Analysis, AnalysisResult, BatchAnalysis
from .forms import AnalysisForm, ResultEditForm, BatchAnalysisForm
from django.views.generic import UpdateView, DetailView
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from .services import generate_result_pdf
from analysis.loggers import logger
from django.views.generic import CreateView

class AnalysisListView(ListView):
    model = Analysis
    template_name = 'analysis/analysis_list.html'
    context_object_name = 'analyses'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('sample', 'created_by')
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
        kwargs['user'] = self.request.user
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

        # Prepare human-readable panel names
        panel_choices = dict(Analysis.BLOOD_PANELS)
        context['display_panels'] = [
            panel_choices.get(panel, panel)
            for panel in analysis.selected_panels
        ] if analysis.selected_panels else []

        return context

    def post(self, request, *args, **kwargs):
        analysis = self.get_object()

        if 'complete_analysis' in request.POST:
            return self._handle_completion(request, analysis)

        return redirect('analysis:detail', pk=analysis.pk)

    def _handle_completion(self, request, analysis):
        if analysis.status in ['completed', 'verified']:
            messages.warning(request, "Analysis is already completed")
            return redirect('analysis:detail', pk=analysis.pk)

        qc_status = request.POST.get('qc_status')
        notes = request.POST.get('notes', '')

        if not qc_status:
            messages.error(request, "QC status is required")
            return redirect('analysis:detail', pk=analysis.pk)

        analysis.status = 'completed'
        analysis.completed_at = timezone.now()
        analysis.qc_status = qc_status
        if notes:
            analysis.notes = notes
        analysis.save()

        messages.success(request, "Analysis marked as completed")
        return redirect('analysis:detail', pk=analysis.pk)


class AnalysisUpdateView(UpdateView):
    model = Analysis
    form_class = AnalysisForm
    template_name = 'analysis/analysis_form.html'

    def get_success_url(self):
        return reverse_lazy('analysis:detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Analyse mise à jour avec succès!')
        return response
# analysis/views.py


class ResultDetailView(DetailView):
    model = AnalysisResult
    template_name = 'analysis/result_detail.html'
    context_object_name = 'result'

class ResultUpdateView(PermissionRequiredMixin, UpdateView):
    model = AnalysisResult
    fields = ['formatted_data', 'is_approved']
    template_name = 'analysis/result_edit.html'
    permission_required = 'analysis.change_analysisresult'

    def form_valid(self, form):
        form.instance.approved_by = self.request.user
        return super().form_valid(form)





def result_pdf(request, pk):
    result = get_object_or_404(AnalysisResult, pk=pk)
    return generate_result_pdf(result)




class ResultEditView(PermissionRequiredMixin, UpdateView):
    model = AnalysisResult
    form_class = ResultEditForm  # Now properly referenced
    template_name = 'analysis/result_edit.html'
    permission_required = 'analysis.change_analysisresult'
    success_url = reverse_lazy('analysis:list')  # Add success URL

    def form_valid(self, form):
        form.instance.modified_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Results updated successfully")
        return response

    def test_log_view(request):
        logger.debug("This is a debug message")
        logger.info("This is an info message")
        logger.warning("This is a warning message")
        logger.error("This is an error message")
        return HttpResponse("Check your logs!")

from django.http import HttpResponse
import logging

logger = logging.getLogger('django')  # Uses Django's default logger

def my_view(request):
    logger.info("Processing request")
    return HttpResponse("Hello World")


class BatchAnalysisCreateView(CreateView):
    model = BatchAnalysis
    form_class = BatchAnalysisForm
    template_name = 'analysis/batch_analysis_form.html'
    success_url = reverse_lazy('analysis:list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


def batch_process(request):
    if request.method == 'POST':
        analysis_ids = request.POST.getlist('analyses')
        analysis_type_id = request.POST.get('analysis_type')

        try:
            # Get selected analyses
            analyses = Analysis.objects.filter(id__in=analysis_ids)

            # Create batch analysis
            batch = BatchAnalysis.objects.create(
                analysis_type_id=analysis_type_id,
                created_by=request.user,
                status='pending'
            )

            # Associate analyses with batch
            batch.analyses.set(analyses)

            # Update analyses status
            analyses.update(status='in_progress')

            return redirect('analysis:batch_detail', pk=batch.pk)

        except Exception as e:
            messages.error(request, f"Error creating batch: {str(e)}")
            return redirect('analysis:list')

class BatchDetailView(DetailView):
    model = BatchAnalysis
    template_name = 'analysis/batch_detail.html'
    context_object_name = 'batch'


from django.contrib import messages
from django.views.generic import DeleteView
from django.urls import reverse_lazy


class BatchDeleteView(DeleteView):
    model = BatchAnalysis
    template_name = 'analysis/batch_confirm_delete.html'
    success_url = reverse_lazy('analysis:list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, f"Batch #{self.get_object().id} was deleted successfully")
        return super().delete(request, *args, **kwargs)


def batch_start(request, pk):
    if request.method == 'POST':
        batch = BatchAnalysis.objects.get(pk=pk)
        batch.status = 'in_progress'
        batch.started_at = timezone.now()
        batch.technician_id = request.POST.get('technician')
        batch.save()
        messages.success(request, f"Batch #{batch.id} processing started")
        return redirect('analysis:batch_detail', pk=pk)


def batch_notes(request, pk):
    if request.method == 'POST':
        batch = BatchAnalysis.objects.get(pk=pk)
        batch.notes = request.POST.get('notes', '')
        batch.save()
        messages.success(request, "Batch notes updated")
        return redirect('analysis:batch_detail', pk=pk)