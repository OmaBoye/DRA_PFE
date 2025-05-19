from django.urls import path
from .views import TurnaroundTimeReport, sample_throughput

urlpatterns = [
    path('analytics/turnaround/', TurnaroundTimeReport.as_view(), name='turnaround_report'),
    path('analytics/throughput/', sample_throughput, name='throughput_report'),
]