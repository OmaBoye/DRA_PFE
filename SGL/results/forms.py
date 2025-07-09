from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Result
from analysis.models import Analysis
import json


class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['status', 'notes', 'test_date']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'validated_by': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'test_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')

        # Add dynamic fields for each test parameter
        if instance and hasattr(instance, 'values'):
            for param, value in instance.values.items():
                field_name = f'values_{param}'
                self.fields[field_name] = forms.CharField(
                    initial=value,
                    required=False,
                    widget=forms.TextInput(attrs={
                        'class': 'form-control form-control-sm',
                        'data-reference-range': self._get_reference_range(param)
                    }),
                    label=param
                )

    def _get_reference_range(self, parameter):
        """Helper to get reference ranges for validation"""
        ranges = {
            'WBC': '4.0-11.0', 'RBC': '4.2-6.1', 'HGB': '12.0-18.0',
            'HCT': '37-54', 'PLT': '150-450', 'GLU': '70-100',
            'CA': '8.5-10.2', 'NA': '135-145', 'K': '3.5-5.2',
            'CL': '98-107', 'CO2': '23-29'
        }
        return ranges.get(parameter, 'N/A')

    def clean(self):
        cleaned_data = super().clean()
        values = {}

        # Collect all the dynamic test value fields
        for field_name, value in cleaned_data.items():
            if field_name.startswith('values_'):
                param = field_name.replace('values_', '')

                # Try to convert to float if numeric
                try:
                    values[param] = float(value) if value else None
                except ValueError:
                    values[param] = value

                # Validate against reference ranges if numeric
                if isinstance(values[param], (int, float)):
                    ref_range = self._get_reference_range(param)
                    if '-' in ref_range:
                        low, high = map(float, ref_range.split('-'))
                        if values[param] < low or values[param] > high:
                            self.add_error(field_name,
                                           f"Value outside reference range ({ref_range})")

        cleaned_data['values'] = values

        # Validate status transitions
        if self.instance and self.instance.pk:
            current_status = self.instance.status
            new_status = cleaned_data.get('status')

            if current_status == 'verified' and new_status != 'verified':
                raise ValidationError("Verified results cannot be changed to another status.")

            if new_status == 'verified' and not cleaned_data.get('validated_by'):
                raise ValidationError("Verifier name is required when status is 'verified'")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Update the values JSON field
        instance.values = self.cleaned_data.get('values', {})

        # Set validated_at if being verified
        if self.cleaned_data.get('status') == 'verified' and not instance.validated_at:
            instance.validated_at = timezone.now()

        if commit:
            instance.save()

        return instance


class ResultFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'statusFilter'
        })
    )

    patient = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Filter by patient...',
            'class': 'form-control'
        })
    )

    date_range = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'dateRangePicker',
            'placeholder': 'Select date range...'
        })
    )