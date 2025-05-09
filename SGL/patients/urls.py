from django.urls import path
from .views import PatientListView, PatientCreateView, PatientDetailView, PatientUpdateView, PatientDeleteView

app_name = 'patients'

urlpatterns = [
    path('', PatientListView.as_view(), name='list'),
    path('create/', PatientCreateView.as_view(), name='create'),
    path('<int:pk>/', PatientDetailView.as_view(), name='detail'),
    path('patients/<int:pk>/update/', PatientUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', PatientDeleteView.as_view(), name='delete'),  # New delete URL
]