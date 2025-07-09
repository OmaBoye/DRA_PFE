from django.urls import path

from . import views
from .views import AnalysisListView, AnalysisCreateView, AnalysisDetailView, AnalysisUpdateView, ResultDetailView, \
    result_pdf, ResultUpdateView, BatchDetailView



app_name = 'analysis'

urlpatterns = [
    path('', AnalysisListView.as_view(), name='list'),
    path('create/', AnalysisCreateView.as_view(), name='create'),
    path('<int:pk>/', AnalysisDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', AnalysisUpdateView.as_view(), name='update'),

    path('results/<int:pk>/', ResultDetailView.as_view(), name='result_detail'),
    path('results/<int:pk>/edit/', ResultUpdateView.as_view(), name='edit_result'),
    path('results/<int:pk>/pdf/', result_pdf, name='result_pdf'),

    path('batch/create/', views.BatchAnalysisCreateView.as_view(), name='batch_create'),
    path('batch/process/', views.batch_process, name='batch_process'),
    path('batch/<int:pk>/', BatchDetailView.as_view(), name='batch_detail'),
    path('batch/<int:pk>/start/', views.batch_start, name='batch_start'),
    path('batch/<int:pk>/notes/', views.batch_notes, name='batch_notes'),
    path('batch/<int:pk>/delete/', views.BatchDeleteView.as_view(), name='batch_delete'),
]