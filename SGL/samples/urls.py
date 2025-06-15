from django.urls import path
from .views import (
    SampleListView,
    SampleCreateView,
    SampleDetailView,
    SampleUpdateView,
    SampleTrackView, SampleDeleteView
)

app_name = 'samples'

urlpatterns = [
    path('', SampleListView.as_view(), name='list'),
    path('create/', SampleCreateView.as_view(), name='create'),
    path('<int:pk>/', SampleDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', SampleUpdateView.as_view(), name='update'),
    path('track/', SampleTrackView.as_view(), name='track'),
    path('<int:pk>/delete/', SampleDeleteView.as_view(), name='delete'),

]
