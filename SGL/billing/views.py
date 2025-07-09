from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
from django.template.loader import render_to_string
from django.db.models import Q
from io import BytesIO
from xhtml2pdf import pisa
import os
import qrcode
from django.core.files import File
from django.db import transaction
import logging
logger = logging.getLogger(__name__)
from SGL import settings
from .models import Bill
from .forms import BillUpdateForm, BillCreateForm
from patients.models import Patient
from analysis.models import Analysis


class BillListView(LoginRequiredMixin, ListView):
    model = Bill
    template_name = 'billing/bill_list.html'
    context_object_name = 'bills'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Bill.STATUS_CHOICES
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        patient_search = self.request.GET.get('patient')

        if status:
            queryset = queryset.filter(status=status)

        if self.request.user.is_staff and patient_search:
            queryset = queryset.filter(
                Q(patient__first_name__icontains=patient_search) |
                Q(patient__last_name__icontains=patient_search)
            )

        return queryset.order_by('-issued_date')


class BillDetailView(LoginRequiredMixin, DetailView):
    model = Bill
    template_name = 'billing/bill_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['analyses'] = self.object.analyses.all().select_related('analysis_type', 'sample')
        return context


def get_patient_analyses(request):
    """HTMX endpoint to fetch unbilled analyses for selected patient"""
    patient_id = request.GET.get('patient_id')
    if not patient_id:
        return HttpResponse("")

    patient = get_object_or_404(Patient, id=patient_id)
    analyses = Analysis.objects.filter(
        sample__patient=patient,
        bill__isnull=True
    ).select_related('analysis_type', 'sample')

    html = render_to_string('billing/includes/analyses_list.html', {
        'analyses': analyses,
        'patient': patient
    })
    return HttpResponse(html)


class BillCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Bill
    form_class = BillCreateForm
    template_name = 'billing/bill_create.html'
    success_url = reverse_lazy('billing:bill_list')

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request, *args, **kwargs):
        # Handle HTMX requests differently if needed
        if request.headers.get('HX-Request'):
            return super().get(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Ensure POST goes to the correct endpoint
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['patients'] = Patient.objects.all().prefetch_related(
            'samples__analyses__analysis_type'
        )
        return context

    def form_valid(self, form):
        try:
            patient_id = self.request.POST.get('patient_id')
            if not patient_id:
                form.add_error(None, "Patient selection is required")
                return self.form_invalid(form)

            patient = get_object_or_404(Patient, id=patient_id)
            form.instance.patient = patient
            form.instance.issued_date = timezone.now()

            response = super().form_valid(form)

            analysis_ids = self.request.POST.getlist('analyses')
            if not analysis_ids:
                form.add_error(None, "At least one analysis must be selected")
                return self.form_invalid(form)

            Analysis.objects.filter(
                id__in=analysis_ids,
                sample__patient=patient
            ).update(bill=self.object)

            # Generate documents
            self.object.generate_qr_code()
            generate_bill_pdf(self.object)

            messages.success(self.request, f'Bill #{self.object.id} created successfully')
            return response

        except Exception as e:
            logger.error(f"Error creating bill: {str(e)}")
            messages.error(self.request, f"Error creating bill: {str(e)}")
            return self.form_invalid(form)

class BillUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Bill
    form_class = BillUpdateForm
    template_name = 'billing/bill_form.html'

    def test_func(self):
        return self.request.user.is_staff

    def get_success_url(self):
        return reverse('billing:bill_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, f"Bill #{self.object.id} updated successfully")
        return super().form_valid(form)


def print_bill(request, pk):
    bill = get_object_or_404(Bill, pk=pk)

    # Regenerate if requested or missing
    if 'regenerate' in request.GET or not bill.pdf_file or not bill.qr_code:
        try:
            if not bill.qr_code:
                bill.generate_qr_code()

            if not generate_bill_pdf(bill):
                messages.error(request, "Failed to generate PDF")
                return redirect('billing:bill_detail', pk=pk)

            bill.refresh_from_db()
        except Exception as e:
            messages.error(request, f"PDF generation error: {str(e)}")
            return redirect('billing:bill_detail', pk=pk)

    try:
        if bill.pdf_file and os.path.exists(bill.pdf_file.path):
            with open(bill.pdf_file.path, 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type='application/pdf')
                disposition = 'inline' if request.user.is_staff else 'attachment'
                response['Content-Disposition'] = f'{disposition}; filename="bill_{bill.id}.pdf"'
                return response
        else:
            messages.warning(request, "PDF not found, regenerating...")
            return redirect(reverse('billing:print_bill', kwargs={'pk': pk}) + '?regenerate=true')
    except Exception as e:
        messages.error(request, f"Error accessing PDF: {str(e)}")
        return redirect('billing:bill_detail', pk=pk)

def mark_bill_as_paid(request, pk):
    bill = get_object_or_404(Bill, pk=pk)

    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action")
        return redirect('billing:bill_detail', pk=pk)

    if request.method == 'POST':
        bill.status = 'paid'
        bill.paid_date = timezone.now()
        bill.save()
        messages.success(request, f"Bill #{bill.id} marked as paid")
        return redirect('billing:bill_detail', pk=bill.id)

    return render(request, 'billing/bill_confirm_pay.html', {'bill': bill})


def generate_bill_pdf(bill):
    """Generate PDF file for a bill and save it to the model"""
    # Ensure QR code exists
    if not bill.qr_code:
        bill.generate_qr_code()
        bill.save()

    context = {
        'bill': bill,
        'logo_path': os.path.join(settings.STATIC_ROOT, 'img/logo.png'),
        'MEDIA_URL': settings.MEDIA_URL,
        'SITE_NAME': getattr(settings, 'SITE_NAME', ''),
        'SITE_ADDRESS': getattr(settings, 'SITE_ADDRESS', ''),
        'SITE_PHONE': getattr(settings, 'SITE_PHONE', ''),
        'SITE_EMAIL': getattr(settings, 'SITE_EMAIL', '')
    }

    html = render_to_string('billing/bill_pdf_template.html', context)
    result = BytesIO()

    pdf = pisa.pisaDocument(
        BytesIO(html.encode("UTF-8")),
        result,
        link_callback=lambda uri, _: uri.replace(
            settings.MEDIA_URL,
            os.path.join(settings.MEDIA_ROOT, '')
        )
    )

    if not pdf.err:
        pdf_dir = os.path.join(settings.MEDIA_ROOT, 'bills/pdfs')
        os.makedirs(pdf_dir, exist_ok=True)

        file_path = os.path.join(pdf_dir, f'bill_{bill.id}.pdf')

        with open(file_path, 'wb') as f:
            f.write(result.getvalue())

        bill.pdf_file.name = f'bills/pdfs/bill_{bill.id}.pdf'
        bill.save()
        return True

    return False



class PatientQRCodeView(LoginRequiredMixin, View):
    def get(self, request, pk):
        patient = get_object_or_404(Patient, pk=pk)
        return JsonResponse({
            'qr_code_url': patient.qr_code.url if patient.qr_code else None
        })