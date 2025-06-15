from django.urls import path
from .views import (
    PatientListView, PatientCreateView,
    PatientDetailView, PatientUpdateView,
    PatientDeleteView, scan_qr,
    PatientResultsPortalView, PatientResultsAPIView,
    patient_list_api,
)

app_name = 'patients'

urlpatterns = [
    path('', PatientListView.as_view(), name='list'),
    path('create/', PatientCreateView.as_view(), name='create'),
    path('<int:pk>/', PatientDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', PatientUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', PatientDeleteView.as_view(), name='delete'),
    path('scan-qr/', scan_qr, name='scan_qr'),
    path('results-portal/', PatientResultsPortalView.as_view(), name='results_portal'),
    path('api/patient/<int:pk>/results/', PatientResultsAPIView.as_view(), name='patient_results_api'),
    path('api/patients/', patient_list_api, name='patient-list-api'),
]