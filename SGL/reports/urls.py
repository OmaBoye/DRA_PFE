from django.urls import path
from .views import ReportListView, ReportGenerateView, ReportDetailView, export_pdf, export_excel, ReportDeleteView, \
    ResultsAPIView

app_name = 'reports'

urlpatterns = [
    path('', ReportListView.as_view(), name='list'),
    path('generate/', ReportGenerateView.as_view(), name='generate'),
    path('<int:pk>/', ReportDetailView.as_view(), name='detail'),
    path('<int:pk>/pdf/', export_pdf, name='export_pdf'),
    path('<int:pk>/excel/', export_excel, name='export_excel'),
    path('<int:pk>/delete/', ReportDeleteView.as_view(), name='delete'),
    path('api/results/', ResultsAPIView.as_view(), name='api_results'),

]