from django.views.generic import CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth.views import LoginView as BaseLoginView


from samples.forms import SampleForm
from .forms import PatientSignupForm, PatientLoginForm
from patients.models import Patient
from samples.models import Sample
from results.models import Result
from django.core.exceptions import PermissionDenied
# Add to the top of views.py
import logging
logger = logging.getLogger(__name__)


class SignUpView(CreateView):
    form_class = PatientSignupForm
    template_name = 'patient_portal/signup.html'
    success_url = reverse_lazy('patient_portal:home')

    def form_valid(self, form):
        logger.debug("Form is valid, saving user")
        response = super().form_valid(form)  # Save the user first

        user = self.object
        logger.debug(f"Created user: {user.username}")

        # Create patient profile
        try:
            patient = Patient.objects.create(
                user_account=user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                date_of_birth=form.cleaned_data['date_of_birth'],
                phone_number=form.cleaned_data['phone_number'],
                email=form.cleaned_data['email'],
                gender=form.cleaned_data['gender']
            )
            logger.debug(f"Created patient profile: {patient}")
        except Exception as e:
            logger.error(f"Error creating patient profile: {e}")
            raise

        # Login the user
        login(self.request, user)
        logger.debug(f"User {user.username} logged in successfully")
        return response

    def form_invalid(self, form):
        logger.error(f"Form invalid with errors: {form.errors}")
        return super().form_invalid(form)


class PortalHomeView(TemplateView):  # Removed LoginRequiredMixin
    template_name = 'patient_portal/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Only show patient-specific data if logged in
        if self.request.user.is_authenticated and hasattr(self.request.user, 'patient_profile'):
            patient = self.request.user.patient_profile
            context['samples'] = Sample.objects.filter(
                patient=patient
            ).order_by('-collection_date')[:5]
            context['results'] = Result.objects.filter(
                sample__patient=patient
            ).order_by('-test_date')[:5]

        return context

class SubmitSampleView(LoginRequiredMixin, CreateView):
    form_class = SampleForm
    template_name = 'patient_portal/submit_sample.html'
    success_url = reverse_lazy('patient_portal:home')

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'patient_profile'):
            raise PermissionDenied("Complete your profile before submitting samples.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.patient = self.request.user.patient_profile
        return super().form_valid(form)


class ResultDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'patient_portal/result_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if 'token' in kwargs:  # QR access
            context['result'] = Result.objects.get(
                sample__patient__qr_token=kwargs['token']
            )
        else:  # Logged-in access
            if not hasattr(self.request.user, 'patient_profile'):
                raise PermissionDenied("Patient profile not found.")

            context['result'] = Result.objects.get(
                pk=kwargs['pk'],
                sample__patient=self.request.user.patient_profile
            )

        return context


class PatientLoginView(BaseLoginView):
    template_name = 'patient_portal/login.html'
    authentication_form = PatientLoginForm
    redirect_authenticated_user = True  # Important for redirects

    def form_valid(self, form):
        """Security check complete. Log the user in."""
        login(self.request, form.get_user())
        logger.debug(f"User {form.get_user().username} logged in successfully")
        return redirect(self.get_success_url())

    def get_success_url(self):
        # Ensure user has profile before redirecting
        if hasattr(self.request.user, 'patient_profile'):
            return reverse_lazy('patient_portal:home')
        return reverse_lazy('patient_portal:signup')