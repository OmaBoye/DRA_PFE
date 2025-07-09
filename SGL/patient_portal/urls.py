# patient_portal/urls.py
from django.urls import path
from . import views

app_name = 'patient_portal'

urlpatterns = [
    path('results/<str:token>/',
         views.PatientResultsPortalView.as_view(),
         name='results_portal'),
    path('print/<str:token>/<int:result_id>/',
         views.print_patient_result,
         name='print_result'),
    path('api/<str:token>/',
         views.PatientPortalAPIView.as_view(),
         name='portal_api'),
]