from django import forms
from .models import Analysis, AnalysisType
from samples.models import Sample


class AnalysisForm(forms.ModelForm):
    panels = forms.MultipleChoiceField(
        choices=Analysis.BLOOD_PANELS,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Blood Panels'
    )

    class Meta:
        model = Analysis
        fields = ['sample', 'analysis_type', 'technician', 'notes', 'priority', 'due_date', 'panels']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Initialize analysis types based on sample
        if self.instance.pk and self.instance.sample:
            self.fields['analysis_type'].queryset = AnalysisType.objects.filter(
                sample_types=self.instance.sample.sample_type
            )
        else:
            self.fields['analysis_type'].queryset = AnalysisType.objects.none()

        # Initialize panels if editing
        if self.instance.pk and self.instance.selected_panels:
            self.fields['panels'].initial = self.instance.selected_panels