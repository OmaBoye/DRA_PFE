# results/urls.py
from django.urls import path
from .views import (
    ResultListView,
    ResultCreateView,
    ResultDetailView,
    ResultUpdateView,
    validate_result,
    print_result,
    generate_qr_code,

)

app_name = 'results'

urlpatterns = [
    path('', ResultListView.as_view(), name='list'),
    path('create/', ResultCreateView.as_view(), name='create'),
    path('<int:pk>/', ResultDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', ResultUpdateView.as_view(), name='update'),
    path('<int:pk>/validate/', validate_result, name='validate'),
    path('<int:pk>/print/', print_result, name='print'),
    # Add these new paths
    path('<int:pk>/generate-qr/', generate_qr_code, name='generate_qr'),
]