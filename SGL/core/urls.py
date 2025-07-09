from django.urls import path, include
from . import views
from .tests import test_counts
from .views import DashboardView
app_name = 'core'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('integrations/', include('integrations.urls')),
    path('test-counts/', test_counts),

    path('scan-qr/', views.scan_unified_qr, name='scan_unified_qr'),
    path('qr-preview/', views.generate_qr_preview, name='qr_preview'),

]