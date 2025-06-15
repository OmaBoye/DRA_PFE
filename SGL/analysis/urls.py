from django.urls import path

from . import views
from .views import AnalysisListView, AnalysisCreateView, AnalysisDetailView, AnalysisUpdateView, get_analysis_types

app_name = 'analysis'

urlpatterns = [
    path('', AnalysisListView.as_view(), name='list'),
    path('create/', AnalysisCreateView.as_view(), name='create'),
    path('<int:pk>/', AnalysisDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', AnalysisUpdateView.as_view(), name='update'),
    path('get-analysis-types/', get_analysis_types, name='get_analysis_types'),
path('samples/<int:sample_id>/type/', views.get_sample_type, name='sample_type'),
]