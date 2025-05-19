from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from .models import Patient
from .forms import PatientForm
from django.http import JsonResponse
from pyzbar.pyzbar import decode
from PIL import Image
from django.views.generic import TemplateView
from django.http import JsonResponse
from results.models import Result
import cv2
import numpy as np

class PatientListView(ListView):
    model = Patient
    template_name = 'patients/patient_list.html'
    context_object_name = 'patients'
    paginate_by = 20

class PatientCreateView(CreateView):
    model = Patient
    form_class = PatientForm
    template_name = 'patients/patient_form.html'
    success_url = reverse_lazy('patients:list')

class PatientDetailView(DetailView):
    model = Patient
    template_name = 'patients/patient_detail.html'
    context_object_name = 'patient'

class PatientUpdateView(UpdateView):
    model = Patient
    form_class = PatientForm
    template_name = 'patients/patient_form.html'
    success_url = reverse_lazy('patients:list')

class PatientDeleteView(DeleteView):
    model = Patient
    template_name = 'patients/patient_confirm_delete.html'  # Create this template
    success_url = reverse_lazy('patients:list')

def scan_qr(request):
    if request.method == 'POST' and request.FILES.get('qr_image'):
        uploaded_file = request.FILES['qr_image']
        image = Image.open(uploaded_file)
        decoded_objects = decode(image)

        if decoded_objects:
            qr_data = decoded_objects[0].data.decode('utf-8')
            if qr_data.startswith("PatientID:"):
                patient_id = qr_data.split(":")[1]
                try:
                    patient = Patient.objects.get(id=patient_id)
                    return JsonResponse({
                        'success': True,
                        'data': {
                            'name': f"{patient.first_name} {patient.last_name}",
                            'dob': patient.date_of_birth.strftime('%d/%m/%Y'),
                            'id': patient.id,
                            'results_url': reverse('patients:patient_results_api', kwargs={'pk': patient.id})
                        }
                    })
                except Patient.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Patient not found'}, status=404)
        return JsonResponse({'success': False, 'error': 'No QR detected or invalid format'}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


class PatientResultsPortalView(TemplateView):
    template_name = 'patients/patient_results_portal.html'


class PatientResultsAPIView(View):
    def get(self, request, pk):
        try:
            patient = Patient.objects.get(pk=pk)
            results = Result.objects.filter(sample__patient=patient).select_related('sample')

            data = {
                'results': [{
                    'id': r.id,
                    'test_name': r.sample.analysis_type.name,
                    'date': r.test_date.strftime('%d/%m/%Y'),
                    'status': r.status
                } for r in results]
            }
            return JsonResponse(data)
        except Patient.DoesNotExist:
            return JsonResponse({'error': 'Patient not found'}, status=404)