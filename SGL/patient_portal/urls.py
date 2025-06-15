# patient_portal/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth.views import LoginView
from .forms import PatientLoginForm

app_name = 'patient_portal'
urlpatterns = [
    # Auth
    path('login/', LoginView.as_view(
        template_name='patient_portal/login.html',
        authentication_form=PatientLoginForm,
    ), name='login'),
    path('home/', views.PortalHomeView.as_view(), name='home'),  # Accessible without login
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.SignUpView.as_view(), name='signup'),

    # Protected portal features (keep these login required)
    path('submit-sample/', views.SubmitSampleView.as_view(), name='submit_sample'),
    path('results/<int:pk>/', views.ResultDetailView.as_view(), name='result_detail'),
    path('results/qr/<str:token>/', views.ResultDetailView.as_view(), name='result_qr_view'),
]