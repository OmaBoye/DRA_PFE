from django import forms
from .models import Result
from samples.models import Sample

class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['sample', 'status', 'test_date', 'completed_date', 'verified_by', 'notes', 'values']
        widgets = {
            'test_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'completed_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'values': forms.Textarea(attrs={'placeholder': 'Enter results as JSON: {"param1": "value1", "param2": "value2"}'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sample'].queryset = Sample.objects.filter(result__isnull=True)