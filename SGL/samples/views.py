import qrcode
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db import transaction
from django.forms import modelformset_factory
from django.utils import timezone
from analysis.models import AnalysisType
from .models import Sample, SampleType, Bill, CustodyLog, Batch
from .forms import SampleForm, RejectSampleForm, CustodyTransferForm, BatchCreateForm
from patients.models import Patient
from .utils import generate_bill_pdf, save_bill_pdf
from users.models import User
from pyzbar.pyzbar import decode
from PIL import Image
from io import BytesIO
import logging
from django.http import HttpResponse
import csv
from openpyxl import Workbook
from django.utils import timezone
from django.contrib import messages


class SampleTrackView(TemplateView):
    template_name = 'samples/sample_track.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['samples'] = Sample.objects.all().order_by('-collection_date')
        return context


class SampleListView(LoginRequiredMixin, ListView):
    model = Sample
    template_name = 'samples/sample_list.html'
    context_object_name = 'samples'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('patient', 'current_technician')
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-collection_date')


class SampleCreateView(LoginRequiredMixin, CreateView):
    model = Sample
    form_class = SampleForm
    template_name = 'samples/sample_form.html'
    success_url = reverse_lazy('samples:list')

    def form_valid(self, form):
        form.instance.barcode = f"SMP-{Sample.objects.count() + 1000}"
        response = super().form_valid(form)

        if form.cleaned_data.get('paid', False):
            bill = Bill.objects.create(
                sample=self.object,
                paid=True,
                amount=100.00
            )
            pdf_content = generate_bill_pdf({
                'sample': self.object,
                'bill': bill
            })
            if pdf_content:
                save_bill_pdf(bill, pdf_content)
                self.object.bill_pdf_url = bill.pdf_file.url

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self, 'object') and hasattr(self.object, 'bill_pdf_url'):
            context['bill_pdf_url'] = self.object.bill_pdf_url
        return context


class SampleDetailView(LoginRequiredMixin, DetailView):
    model = Sample
    template_name = 'samples/sample_detail.html'
    context_object_name = 'sample'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['custody_logs'] = self.object.custody_logs.all().select_related('from_technician', 'to_technician')
        context['batches'] = self.object.batches.all()
        return context


class SampleUpdateView(LoginRequiredMixin, UpdateView):
    model = Sample
    form_class = SampleForm
    template_name = 'samples/sample_form.html'
    context_object_name = 'sample'

    def get_success_url(self):
        return reverse_lazy('samples:detail', kwargs={'pk': self.object.pk})


class SampleDeleteView(LoginRequiredMixin, DeleteView):
    model = Sample
    template_name = 'samples/sample_confirm_delete.html'
    success_url = reverse_lazy('samples:list')


class RejectSampleView(LoginRequiredMixin, UpdateView):
    model = Sample
    form_class = RejectSampleForm
    template_name = 'samples/reject_sample.html'

    def get_initial(self):
        return {'status': 'rejected'}

    def form_valid(self, form):
        messages.success(self.request, f"Sample {self.object.barcode} has been rejected")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('samples:detail', kwargs={'pk': self.object.pk})


class TransferCustodyView(LoginRequiredMixin, CreateView):
    model = CustodyLog
    form_class = CustodyTransferForm
    template_name = 'samples/transfer_custody.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sample'] = get_object_or_404(Sample, pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        sample = get_object_or_404(Sample, pk=self.kwargs['pk'])
        with transaction.atomic():
            custody_log = form.save(commit=False)
            custody_log.sample = sample
            custody_log.from_technician = self.request.user
            custody_log.save()

            sample.current_technician = custody_log.to_technician
            sample.save()

        messages.success(self.request, f"Custody transferred to {custody_log.to_technician}")
        return redirect('samples:detail', pk=sample.pk)


class BatchListView(LoginRequiredMixin, ListView):
    model = Batch
    template_name = 'samples/batch_list.html'
    context_object_name = 'batches'
    paginate_by = 20

    def get_queryset(self):
        return Batch.objects.all().prefetch_related('samples').order_by('-created_at')


class BatchCreateView(LoginRequiredMixin, CreateView):
    model = Batch
    form_class = BatchCreateForm
    template_name = 'samples/batch_create.html'
    success_url = reverse_lazy('samples:batch_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        batch = form.save(commit=False)
        batch.created_by = self.request.user
        batch.save()
        form.save_m2m()  # Save the many-to-many data
        messages.success(self.request, f"Batch {batch.name} created successfully")
        return redirect('samples:batch_detail', pk=batch.pk)


class BatchDetailView(LoginRequiredMixin, DetailView):
    model = Batch
    template_name = 'samples/batch_detail.html'
    context_object_name = 'batch'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['samples'] = self.object.samples.all().select_related('patient')
        return context


class BatchProcessView(LoginRequiredMixin, UpdateView):
    model = Batch
    fields = []
    template_name = 'samples/batch_process.html'

    def form_valid(self, form):
        batch = form.save(commit=False)
        batch.is_processed = True
        batch.processed_at = timezone.now()
        batch.save()

        for sample in batch.samples.all():
            sample.status = 'processing'

            # Generate QR code if not exists
            if not sample.qr_code:
                sample.generate_qr_code()

            sample.save()

        messages.success(self.request,
                         f"Processed batch {batch.name} with {batch.samples.count()} samples")
        return redirect('samples:batch_detail', pk=batch.pk)

def create_sample(request):
    if request.method == 'POST':
        form = SampleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('samples:list')
    else:
        form = SampleForm()

    patients = Patient.objects.all().order_by('last_name')
    return render(request, 'samples/sample_form.html', {
        'form': form,
        'patients': patients
    })


def get_analysis_types(request):
    """AJAX endpoint for getting analysis types based on sample"""
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


def get_sample_type(request, sample_id):
    """AJAX endpoint for checking sample type"""
    try:
        sample = Sample.objects.get(id=sample_id)
        return JsonResponse({
            'sample_type': sample.sample_type.first().name.lower() if sample.sample_type.exists() else ''
        })
    except Sample.DoesNotExist:
        return JsonResponse({'error': 'Sample not found'}, status=404)


logger = logging.getLogger(__name__)


def scan_sample_qr(request):
    if request.method == 'POST' and request.FILES.get('qr_image'):
        try:
            # Open the uploaded image
            image = Image.open(request.FILES['qr_image'])
            decoded_objects = decode(image)

            if not decoded_objects:
                return JsonResponse({'error': 'No QR code detected'}, status=400)

            # Extract data from QR code
            qr_data = decoded_objects[0].data.decode('utf-8')

            # Parse QR data (example format: "Patient:123|token Sample:456")
            try:
                patient_part, sample_part = [p.strip() for p in qr_data.split('Sample:')]
                patient_id = patient_part.split('Patient:')[1].split('|')[0]
                sample_barcode = sample_part.split()[0]

                # Get objects from database
                patient = Patient.objects.get(id=patient_id)
                sample = Sample.objects.get(barcode=sample_barcode, patient=patient)

                # Prepare response data
                response_data = {
                    'success': True,
                    'sample': {
                        'barcode': sample.barcode,
                        'collection_date': sample.collection_date.strftime('%Y-%m-%d'),
                        'status': sample.get_status_display(),
                        'url': sample.get_absolute_url()
                    },
                    'patient': {
                        'id': patient.id,
                        'name': patient.full_name,
                        'dob': patient.date_of_birth.strftime('%Y-%m-%d')
                    }
                }
                return JsonResponse(response_data)

            except (IndexError, ValueError, Patient.DoesNotExist, Sample.DoesNotExist) as e:
                logger.warning(f"QR data parsing failed: {str(e)}")
                return JsonResponse({'error': 'Invalid QR code format'}, status=400)

        except Exception as e:
            logger.error(f"QR scan error: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Processing error'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


def export_samples_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="echantillons_{timezone.now().date()}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Code-barres', 'Patient', 'Type(s)',
        'Date prélèvement', 'Statut', 'Motif rejet'
    ])

    samples = Sample.objects.all()
    if request.GET.get('status'):
        samples = samples.filter(status=request.GET['status'])

    for sample in samples:
        writer.writerow([
            sample.barcode,
            sample.patient.full_name,
            sample.get_sample_types_display(),
            sample.collection_date.strftime('%d/%m/%Y %H:%M'),
            sample.get_status_display(),
            sample.get_rejection_reason_display() if sample.status == 'rejected' else ''
        ])

    return response


def export_samples_excel(request):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="echantillons_{timezone.now().date()}.xlsx"'

    wb = Workbook()
    ws = wb.active
    ws.title = "Échantillons"

    headers = [
        'Code-barres', 'Patient', 'Type(s)',
        'Date prélèvement', 'Statut', 'Motif rejet'
    ]
    ws.append(headers)

    samples = Sample.objects.all()
    if request.GET.get('status'):
        samples = samples.filter(status=request.GET['status'])

    for sample in samples:
        ws.append([
            sample.barcode,
            sample.patient.full_name,
            sample.get_sample_types_display(),
            sample.collection_date,
            sample.get_status_display(),
            sample.get_rejection_reason_display() if sample.status == 'rejected' else ''
        ])

    wb.save(response)
    return response


# Bulk actions
@login_required
def bulk_action(request):
    if request.method == 'POST':
        sample_ids = request.POST.getlist('sample_ids')
        action = request.POST.get('bulk-action')

        if not sample_ids:
            messages.error(request, "Aucun échantillon sélectionné")
            return redirect('samples:list')

        samples = Sample.objects.filter(id__in=sample_ids)

        if action.startswith('change_status:'):
            new_status = action.split(':')[1]
            samples.update(status=new_status)
            messages.success(request, f"{samples.count()} échantillons mis à jour")

        elif action == 'add_to_batch':
            # Implement batch creation logic
            pass

        elif action == 'add_to_existing_batch':
            batch_id = request.POST.get('batch_id')
            if batch_id:
                batch = get_object_or_404(Batch, id=batch_id)
                batch.samples.add(*samples)
                messages.success(request, f"{samples.count()} échantillons ajoutés au lot {batch.name}")
                return redirect('samples:batch_detail', pk=batch_id)
            else:
                messages.error(request, "Aucun lot sélectionné")

        return redirect('samples:list')

    return redirect('samples:list')


# QR customization
@login_required
def customize_qr(request, pk):
    sample = get_object_or_404(Sample, pk=pk)

    if request.method == 'POST':
        fill_color = request.POST.get('fill_color', '#000000')
        back_color = request.POST.get('back_color', '#FFFFFF')
        box_size = int(request.POST.get('box_size', 6))
        border = int(request.POST.get('border', 4))

        try:
            # Regenerate QR with custom settings
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=box_size,
                border=border,
            )

            qr_data = f"""
            PATIENT_ID:{sample.patient.id}
            PATIENT_TOKEN:{sample.patient.qr_token}
            SAMPLE_ID:{sample.barcode}
            COLLECTION_DATE:{sample.collection_date.date()}
            STATUS:{sample.status}
            """

            qr.add_data(qr_data.strip())
            qr.make(fit=True)

            img = qr.make_image(fill_color=fill_color, back_color=back_color)
            buffer = BytesIO()
            img.save(buffer, format="PNG")

            sample.qr_code.save(
                f'sample_{sample.barcode}_custom.png',
                File(buffer),
                save=True
            )

            messages.success(request, "QR Code personnalisé généré avec succès")
        except Exception as e:
            messages.error(request, f"Erreur lors de la génération: {str(e)}")

        return redirect('samples:detail', pk=pk)

    return redirect('samples:detail', pk=pk)