from django import forms
from .models import Analysis, AnalysisType
from samples.models import Sample

class AnalysisForm(forms.ModelForm):
    class Meta:
        model = Analysis
        fields = ['sample', 'analysis_type', 'technician', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'sample' in self.data:
            try:
                sample_id = int(self.data.get('sample'))
                sample = Sample.objects.get(id=sample_id)
                self.fields['analysis_type'].queryset = AnalysisType.objects.filter(
                    sample_types=sample.sample_type
                )
            except (ValueError, TypeError, Sample.DoesNotExist):
                pass
        elif self.instance.pk:
            self.fields['analysis_type'].queryset = AnalysisType.objects.filter(
                sample_types=self.instance.sample.sample_type
            )