from io import BytesIO
import qrcode
from django.core.files import File
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.urls import reverse_lazy
from .models import Result
from .forms import ResultForm
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from fpdf import FPDF
from django.contrib import messages
from django.utils import timezone
from django.utils.safestring import mark_safe
from equipment.services.julius_pdf import JuliusPDFGenerator



class ResultListView(ListView):
    model = Result
    template_name = 'results/result_list.html'
    context_object_name = 'results'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Result.STATUS_CHOICES
        return context

    def get_status_choices(self):
        return Result.STATUS_CHOICES


class ResultCreateView(CreateView):
    model = Result
    form_class = ResultForm
    template_name = 'results/result_form.html'
    success_url = reverse_lazy('results:list')


class ResultDetailView(DetailView, UpdateView):
    model = Result
    form_class = ResultForm
    template_name = 'results/result_detail.html'
    context_object_name = 'result'

    def get_success_url(self):
        return reverse_lazy('results:detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        result = self.object

        # Prepare formatted results data
        formatted_results = []
        for param, value in result.values.items():
            formatted_results.append({
                'parameter': param,
                'value': value,
                'unit': self.get_unit(param),
                'reference_range': self.get_reference_range(param),
                'is_abnormal': self.is_abnormal_value(param, value)
            })

        context['formatted_results'] = formatted_results
        context['form'] = self.get_form()
        return context

    def get_unit(self, parameter):
        """Map parameters to their units"""
        units = {
            'WBC': '10³/μL', 'RBC': '10⁶/μL', 'HGB': 'g/dL', 'HCT': '%', 'PLT': '10³/μL',
            'GLU': 'mg/dL', 'CA': 'mg/dL', 'NA': 'mmol/L', 'K': 'mmol/L', 'CL': 'mmol/L', 'CO2': 'mmol/L'
        }
        return units.get(parameter, '')

    def get_reference_range(self, parameter):
        """Clinical reference ranges"""
        ranges = {
            'WBC': '4.0-11.0', 'RBC': '4.2-6.1', 'HGB': '12.0-18.0', 'HCT': '37-54', 'PLT': '150-450',
            'GLU': '70-100', 'CA': '8.5-10.2', 'NA': '135-145', 'K': '3.5-5.2', 'CL': '98-107', 'CO2': '23-29'
        }
        return ranges.get(parameter, 'N/A')

    def is_abnormal_value(self, parameter, value):
        """Check if value is outside reference range"""
        ref_range = self.get_reference_range(parameter)
        if '-' in ref_range:
            try:
                value_float = float(value)
                low, high = map(float, ref_range.split('-'))
                return value_float < low or value_float > high
            except (ValueError, TypeError):
                return False
        return False

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Résultats mis à jour avec succès")
        return super().form_valid(form)


class ResultUpdateView(UpdateView):
    model = Result
    form_class = ResultForm
    template_name = 'results/result_form.html'
    context_object_name = 'result'

    def form_valid(self, form):
        print("Form is valid, saving data...")
        return super().form_valid(form)

    def form_invalid(self, form):
        print("Form errors:", form.errors)
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('results:detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['editing'] = True
        return context


def validate_result(request, pk):
    result = get_object_or_404(Result, pk=pk)
    result.status = 'verified'
    result.validated_by = request.user.get_full_name() or request.user.username
    result.validated_at = timezone.now()
    result.save()
    messages.success(request, "Résultat validé avec succès")
    return redirect('results:detail', pk=pk)


def print_result(request, pk):
    result = get_object_or_404(Result, pk=pk)

    try:
        # Generate PDF using Julius AI
        pdf_content = JuliusPDFGenerator.generate_result_pdf(result)

        # Prepare response
        response = HttpResponse(pdf_content, content_type='application/pdf')
        filename = f"LabResult_{result.sample.barcode}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        messages.error(request, f"PDF generation failed: {str(e)}")
        return redirect('results:detail', pk=pk)


def generate_qr_code(request, pk):
    result = get_object_or_404(Result, pk=pk)

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(
        f"Result ID: {result.id}\nPatient: {result.sample.patient.full_name}\nDate: {result.created_at.strftime('%Y-%m-%d')}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Save to model
    buffer = BytesIO()
    img.save(buffer)
    filename = f'qr_{result.id}.png'
    result.qr_code.save(filename, File(buffer), save=True)

    messages.success(request, "QR code généré avec succès")
    return redirect('results:detail', pk=pk)