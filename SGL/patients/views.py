from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Patient
from .forms import PatientForm
from django.http import JsonResponse
from pyzbar.pyzbar import decode
from PIL import Image
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
                            'name': patient.full_name,
                            'dob': patient.date_of_birth.strftime('%d/%m/%Y'),
                            'id': patient.id
                        }
                    })
                except Patient.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Patient not found'}, status=404)
        return JsonResponse({'success': False, 'error': 'No QR detected or invalid format'}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)