from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, Http404, HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.db import models, transaction
import logging
from datetime import timedelta
import secrets
from pyzbar.pyzbar import decode
from PIL import Image
import json

# Models
from .models import Patient
from results.models import Result
from analysis.models import Analysis

# Forms
from .forms import PatientForm

logger = logging.getLogger(__name__)


class PatientListView(LoginRequiredMixin, ListView):
    model = Patient
    template_name = 'patients/patient_list.html'
    context_object_name = 'patients'
    paginate_by = 20
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        search_term = self.request.GET.get('search')
        if search_term:
            queryset = queryset.filter(
                models.Q(first_name__icontains=search_term) |
                models.Q(last_name__icontains=search_term) |
                models.Q(phone_number__icontains=search_term)
            )
        return queryset


class PatientCreateView(LoginRequiredMixin, CreateView):
    model = Patient
    form_class = PatientForm
    template_name = 'patients/patient_form.html'
    success_url = reverse_lazy('patients:list')

    @transaction.atomic
    def form_valid(self, form):
        try:
            patient = form.save(commit=False)
            if not patient.qr_token:
                patient.qr_token = secrets.token_urlsafe(32)
                patient.qr_token_expires = timezone.now() + timedelta(days=30)
            patient.save()

            messages.success(self.request, f"Patient {patient.full_name} created successfully!")
            logger.info(f"Created patient ID: {patient.id}")
            return redirect(self.get_success_url())

        except Exception as e:
            logger.error(f"Error creating patient: {str(e)}")
            messages.error(self.request, "An error occurred while saving the patient.")
            return self.form_invalid(form)


class PatientDetailView(LoginRequiredMixin, DetailView):
    model = Patient
    template_name = 'patients/patient_detail.html'
    context_object_name = 'patient'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_samples'] = self.object.samples.all().order_by('-collection_date')[:5]
        context['recent_results'] = Result.objects.filter(
            sample__patient=self.object
        ).select_related('sample')[:5]
        return context


class PatientUpdateView(LoginRequiredMixin, UpdateView):
    model = Patient
    form_class = PatientForm
    template_name = 'patients/patient_form.html'

    def get_success_url(self):
        messages.success(self.request, f"Patient {self.object.full_name} updated successfully")
        return reverse('patients:detail', kwargs={'pk': self.object.pk})


class PatientDeleteView(LoginRequiredMixin, DeleteView):
    model = Patient
    template_name = 'patients/patient_confirm_delete.html'
    success_url = reverse_lazy('patients:list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Patient deleted successfully")
        return super().delete(request, *args, **kwargs)


def scan_qr(request):
    if request.method == 'POST' and request.FILES.get('qr_image'):
        try:
            uploaded_file = request.FILES['qr_image']
            image = Image.open(uploaded_file)
            decoded_objects = decode(image)

            if decoded_objects:
                qr_data = json.loads(decoded_objects[0].data.decode('utf-8'))

                if qr_data.get('type') == 'patient_portal':
                    try:
                        patient = Patient.objects.get(id=qr_data['patient_id'])
                        return JsonResponse({
                            'success': True,
                            'data': {
                                'name': patient.full_name,
                                'dob': patient.date_of_birth.strftime('%d/%m/%Y'),
                                'id': patient.id,
                                'portal_url': qr_data['url']
                            }
                        })
                    except Patient.DoesNotExist:
                        return JsonResponse({'success': False, 'error': 'Patient not found'}, status=404)

            return JsonResponse({'success': False, 'error': 'Invalid QR code format'}, status=400)

        except Exception as e:
            logger.error(f"QR scan error: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


class PatientResultsAPIView(View):
    def get(self, request, pk):
        try:
            patient = Patient.objects.get(pk=pk)
            results = Result.objects.filter(
                sample__patient=patient
            ).select_related('sample__analysis_type')

            data = {
                'results': [{
                    'id': r.id,
                    'test_name': r.sample.analysis_type.name,
                    'date': r.test_date.strftime('%d/%m/%Y'),
                    'status': r.status,
                    'report_url': reverse('results:detail', kwargs={'pk': r.id})
                    if r.status == 'completed' else None
                } for r in results]
            }
            return JsonResponse(data)
        except Patient.DoesNotExist:
            return JsonResponse({'error': 'Patient not found'}, status=404)


def patient_list_api(request):
    patients = Patient.objects.all().order_by('last_name', 'first_name').values(
        'id', 'first_name', 'last_name', 'date_of_birth'
    )
    return JsonResponse(list(patients), safe=False)