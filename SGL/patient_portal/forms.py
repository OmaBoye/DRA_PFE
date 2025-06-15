from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from patient_portal.models import PatientUser
from patients.models import Patient


class PatientSignupForm(UserCreationForm):
    # User fields
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    phone_number = forms.CharField(max_length=17, widget=forms.TextInput(attrs={'class': 'form-control'}))
    gender = forms.ChoiceField(choices=Patient.GENDER_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta(UserCreationForm.Meta):
        model = PatientUser
        fields = ('username', 'email', 'password1', 'password2',
                 'first_name', 'last_name', 'date_of_birth',
                 'phone_number', 'gender')

class PatientLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})