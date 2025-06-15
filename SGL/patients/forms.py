from django import forms
from .models import Patient
from django.utils import timezone
from datetime import timedelta
import secrets


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        exclude = ['qr_code', 'qr_token', 'qr_token_expires']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'medical_history': forms.Textarea(attrs={'rows': 3}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.qr_token:
            instance.qr_token = secrets.token_urlsafe(32)
            instance.qr_token_expires = timezone.now() + timedelta(days=30)
        if commit:
            instance.save()
        return instance