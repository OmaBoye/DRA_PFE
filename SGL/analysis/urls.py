from django.urls import path
from .views import AnalysisListView, AnalysisCreateView, AnalysisDetailView, AnalysisUpdateView

app_name = 'analysis'

urlpatterns = [
    path('', AnalysisListView.as_view(), name='list'),
    path('create/', AnalysisCreateView.as_view(), name='create'),
    path('<int:pk>/', AnalysisDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', AnalysisUpdateView.as_view(), name='update'),
]