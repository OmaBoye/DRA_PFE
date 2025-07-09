from django.urls import path
from .views import EHRPatientAPI, EHRResultsWebhook

urlpatterns = [
    path('api/ehr/patients/', EHRPatientAPI.as_view(), name='ehr_patient_api'),
    path('api/ehr/webhook/', EHRResultsWebhook.as_view(), name='ehr_results_webhook'),
]