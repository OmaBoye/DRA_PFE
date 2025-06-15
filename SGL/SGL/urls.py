from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView, LogoutView
from core.views import DashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', DashboardView.as_view(), name='dashboard'),
    path('accounts/login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', LogoutView.as_view(), name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('patients/', include('patients.urls', namespace='patients')),
    path('samples/', include('samples.urls', namespace='samples')),
    path('analysis/', include('analysis.urls', namespace='analysis')),
    path('results/', include('results.urls', namespace='results')),
    path('reports/', include('reports.urls', namespace='reports')),
    path('users/', include('users.urls', namespace='users')),
    path('portal/', include('patient_portal.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)