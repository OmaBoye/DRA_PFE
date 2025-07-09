from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username',
            'email',
            'password1',
            'password2',
            'first_name',
            'last_name',
            'phone_number',
            'role',
            'is_active',
            'is_patient',
            'date_of_birth',
            'address'
        )
        labels = {
            'role': _('User Role'),
            'is_patient': _('Patient Status'),
        }
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Limit role choices to staff roles only
        self.fields['role'].choices = [
            (User.Role.ADMIN, _('Administrator')),
            (User.Role.BIOLOGIST, _('Biologist')),
            (User.Role.TECHNICIAN, _('Laboratory Technician')),
            (User.Role.RECEPTIONIST, _('Receptionist')),
        ]

        # Remove fields we don't want in the form
        for field in ['groups', 'user_permissions', 'is_superuser', 'is_staff']:
            if field in self.fields:
                del self.fields[field]

        # Make email required
        self.fields['email'].required = True

        # Set help texts
        self.fields['username'].help_text = _('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.')
        self.fields['password1'].help_text = _(
            "Your password must contain at least 8 characters, "
            "can't be entirely numeric, and shouldn't be too common."
        )

        # Add placeholder texts
        self.fields['phone_number'].widget.attrs['placeholder'] = _('e.g. +1234567890')
        self.fields['date_of_birth'].widget.attrs['placeholder'] = _('YYYY-MM-DD')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'role',
            'is_active',
            'is_staff',
            'is_patient',
            'date_of_birth',
            'address',
        )
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Limit role choices to staff roles only
        self.fields['role'].choices = [
            (User.Role.ADMIN, _('Administrator')),
            (User.Role.BIOLOGIST, _('Biologist')),
            (User.Role.TECHNICIAN, _('Laboratory Technician')),
            (User.Role.RECEPTIONIST, _('Receptionist')),
        ]

        # Remove fields we don't want in the form
        for field in ['groups', 'user_permissions', 'is_superuser']:
            if field in self.fields:
                del self.fields[field]

        # Make email required
        self.fields['email'].required = True

        # Password field handling
        password = self.fields.get('password')
        if password:
            password.help_text = _(
                "Raw passwords are not stored. You can change the password using "
                "<a href=\"../password/\">this form</a>."
            )

        # Add placeholder texts
        self.fields['phone_number'].widget.attrs['placeholder'] = _('e.g. +1234567890')
        self.fields['date_of_birth'].widget.attrs['placeholder'] = _('YYYY-MM-DD')

        # Only allow admins to change is_staff status
        if not self.instance.is_superuser and 'is_staff' in self.fields:
            if not self.current_user.is_superuser:
                del self.fields['is_staff']

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)