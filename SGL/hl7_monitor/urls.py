# hl7_monitor/urls.py
from django.urls import path, include
from .views import MessageDashboard, MessageDetail, FHIRLogView

app_name = 'hl7-monitor'

urlpatterns = [
    path('', MessageDashboard.as_view(), name='dashboard'),
    path('message/<int:pk>/', MessageDetail.as_view(), name='detail'),
    path('fhir-logs/', FHIRLogView.as_view(), name='fhir-logs'),
]

# SGL/urls.py
urlpatterns += [
    path('hl7-monitor/', include('hl7_monitor.urls')),
]