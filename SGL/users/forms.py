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
            'is_patient',
            'date_of_birth',
            'address'
        )
        labels = {
            'role': _('User Role'),
            'is_patient': _('Patient Status'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'groups' in self.fields:
            del self.fields['groups']
        if 'user_permissions' in self.fields:
            del self.fields['user_permissions']


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
            'is_superuser',
            'is_patient',
            'date_of_birth',
            'address',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'groups' in self.fields:
            del self.fields['groups']
        if 'user_permissions' in self.fields:
            del self.fields['user_permissions']

        password = self.fields.get('password')
        if password:
            password.help_text = _(
                "Raw passwords are not stored. You can change the password using "
                "<a href=\"../password/\">this form</a>."
            )