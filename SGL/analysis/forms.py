from django import forms
from django.forms import Select
from .models import Analysis, AnalysisResult, BatchAnalysis
from samples.models import Sample
from analysis.models import AnalysisType


class AnalysisForm(forms.ModelForm):
    BLOOD_PANEL_CHOICES = [
        ('cbc', 'Complete Blood Count (CBC)'),
        ('bmp', 'Basic Metabolic Panel (BMP)'),
        ('cmp', 'Complete Metabolic Panel (CMP)'),
        ('electrolyte', 'Electrolyte Panel'),
        ('liver', 'Liver Function Panel'),
        ('lipid', 'Lipid Panel'),
        ('thyroid', 'Thyroid Panel'),
        ('coagulation', 'Coagulation Panel'),
    ]

    panels = forms.MultipleChoiceField(
        choices=BLOOD_PANEL_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Select Blood Panels'
    )

    class Meta:
        model = Analysis
        fields = ['sample', 'analysis_type', 'technician', 'notes', 'priority', 'panels']
        widgets = {
            'sample': Select(attrs={
                'class': 'form-control',
                'hx-get': '/analysis/get-analysis-types/',
                'hx-target': '#id_analysis_type',
                'hx-trigger': 'change'
            }),
            'analysis_type': Select(attrs={'class': 'form-control'}),
            'technician': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter any additional notes...'
            }),
            'priority': Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Set initial values
        if not self.instance.pk:
            self.fields['priority'].initial = 'routine'

        # Filter analysis types based on sample (if provided)
        if 'sample' in self.data:
            try:
                sample_id = int(self.data.get('sample'))
                sample = Sample.objects.get(id=sample_id)
                self.fields['analysis_type'].queryset = AnalysisType.objects.filter(
                    sample_types__in=sample.sample_type.all()
                ).order_by('name')
            except (ValueError, Sample.DoesNotExist):
                pass
        elif self.instance.pk and self.instance.sample:
            self.fields['analysis_type'].queryset = AnalysisType.objects.filter(
                sample_types__in=self.instance.sample.sample_type.all()
            ).order_by('name')

        # Set initial panels if editing
        if self.instance.pk and self.instance.selected_panels:
            self.fields['panels'].initial = self.instance.selected_panels

    def clean(self):
        cleaned_data = super().clean()
        sample = cleaned_data.get('sample')
        analysis_type = cleaned_data.get('analysis_type')
        panels = cleaned_data.get('panels', [])

        # Validate sample type matches analysis requirements
        if sample and analysis_type:
            allowed_types = analysis_type.sample_types.all()
            if allowed_types and not sample.sample_type.filter(id__in=allowed_types).exists():
                self.add_error(
                    'sample',
                    f"Invalid sample type for {analysis_type.name}. "
                    f"Allowed: {', '.join([t.name for t in allowed_types])}"
                )

        # Store panels in JSON format
        if panels:
            cleaned_data['selected_panels'] = panels

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set created_by if new analysis
        if not instance.pk:
            instance.created_by = self.user

        # Store selected panels
        if 'selected_panels' in self.cleaned_data:
            instance.selected_panels = self.cleaned_data['selected_panels']

        if commit:
            instance.save()
            self.save_m2m()

        return instance


class AnalysisFilterForm(forms.Form):
    """Form for filtering analyses in the list view"""
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    sample = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sample Barcode'
        })
    )
    date_range = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
class ResultEditForm(forms.ModelForm):
    class Meta:
        model = AnalysisResult
        fields = ['formatted_data', 'is_approved']
        widgets = {
            'formatted_data': forms.Textarea(attrs={
                'class': 'd-none',
                'id': 'formatted-data'  # Matches the template's textarea ID
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['formatted_data'].initial = self.instance.formatted_data

class BatchAnalysisForm(forms.ModelForm):
    class Meta:
        model = BatchAnalysis
        fields = ['analysis_type']
        widgets = {
            'analysis_type': forms.Select(attrs={'class': 'form-control'})
        }