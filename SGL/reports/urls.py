from django.urls import path
from .views import ReportListView, ReportCreateView, ReportDetailView, ReportGenerateView, export_pdf, export_excel

app_name = 'reports'

urlpatterns = [
    path('', ReportListView.as_view(), name='list'),
    path('create/', ReportCreateView.as_view(), name='create'),
    path('generate/', ReportGenerateView.as_view(), name='generate'),
    path('<int:pk>/', ReportDetailView.as_view(), name='detail'),
path('<int:pk>/pdf/', export_pdf, name='export_pdf'),
path('export-excel/', export_excel, name='export_excel'),
]