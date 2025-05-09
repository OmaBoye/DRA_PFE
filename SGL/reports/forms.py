from django import forms
from .models import Report
from results.models import Result

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['result', 'generated_by', 'approved_by', 'notes', 'template_name']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['result'].queryset = Result.objects.filter(report__isnull=True)