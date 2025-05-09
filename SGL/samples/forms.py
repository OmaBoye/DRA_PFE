from django import forms
from .models import Sample
from patients.models import Patient

class SampleForm(forms.ModelForm):
    class Meta:
        model = Sample
        fields = ['patient', 'sample_type', 'collection_date', 'notes']
        widgets = {
            'collection_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['patient'].queryset = Patient.objects.all().order_by('last_name')