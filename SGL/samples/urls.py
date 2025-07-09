from django.urls import path
from .views import export_samples_csv, export_samples_excel, bulk_action, customize_qr

from . import views
from .views import (
    SampleTrackView, SampleListView, SampleCreateView, SampleDetailView,
    SampleUpdateView, SampleDeleteView, create_sample, RejectSampleView,
    TransferCustodyView, BatchListView, BatchCreateView, BatchDetailView,
    BatchProcessView, get_analysis_types, get_sample_type
)

app_name = 'samples'

urlpatterns = [
    # Existing sample URLs
    path('', SampleListView.as_view(), name='list'),
    path('create/', SampleCreateView.as_view(), name='create'),
    path('<int:pk>/', SampleDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', SampleUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', SampleDeleteView.as_view(), name='delete'),
    path('track/', SampleTrackView.as_view(), name='track'),

    # New rejection URL
    path('<int:pk>/reject/', RejectSampleView.as_view(), name='reject'),

    # Custody transfer URLs
    path('<int:pk>/transfer/', TransferCustodyView.as_view(), name='transfer'),

    # Batch processing URLs
    path('batches/', BatchListView.as_view(), name='batch_list'),
    path('batches/create/', BatchCreateView.as_view(), name='batch_create'),
    path('batches/<int:pk>/', BatchDetailView.as_view(), name='batch_detail'),
    path('batches/<int:pk>/process/', BatchProcessView.as_view(), name='batch_process'),

    # AJAX endpoints
    path('get-analysis-types/', get_analysis_types, name='get_analysis_types'),
    path('samples/<int:sample_id>/type/', get_sample_type, name='sample_type'),

    # QR
    path('scan-sample-qr/', views.scan_sample_qr, name='scan_sample_qr'),

    path('export/csv/', export_samples_csv, name='export_csv'),
    path('export/excel/', export_samples_excel, name='export_excel'),
    path('bulk-action/', bulk_action, name='bulk_action'),
    path('<int:pk>/customize-qr/', customize_qr, name='customize_qr'),
]
