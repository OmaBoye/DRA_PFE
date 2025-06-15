from django.urls import path
from .views import ResultListView, ResultCreateView, ResultDetailView, ResultUpdateView

app_name = 'results'

urlpatterns = [
    path('', ResultListView.as_view(), name='list'),
    path('create/', ResultCreateView.as_view(), name='create'),
    path('<int:pk>/', ResultDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', ResultUpdateView.as_view(), name='update'),
]