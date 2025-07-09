from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Report
from results.models import Result
from django.db.models import Q


class ReportForm(forms.ModelForm):
    REPORT_TYPE_CHOICES = [
        ('results', 'Résultats par analyse'),
        ('activity', 'Activité du laboratoire'),
        ('performance', 'Performances'),
    ]

    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]

    report_type = forms.ChoiceField(
        choices=REPORT_TYPE_CHOICES,
        required=True,
        widget=forms.RadioSelect,
        initial='results',
        label="Type de rapport"
    )

    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        required=True,
        widget=forms.Select,
        label="Format"
    )

    # Date fields
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'id': 'id_start_date'
        }),
        label="Date de début",
        initial=timezone.now().replace(day=1)  # First day of current month
    )

    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'id': 'id_end_date'
        }),
        label="Date de fin",
        initial=timezone.now
    )

    # Results selection
    results = forms.ModelMultipleChoiceField(
        queryset=Result.objects.none(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'id': 'id_results',
            'style': 'height: 200px;'
        }),
        required=False,
        label="Résultats disponibles"
    )

    # Conditional fields
    analysis_type = forms.ChoiceField(
        choices=[
            ('', 'Tous les types'),
            ('hematology', 'Hématologie'),
            ('biochemistry', 'Biochimie'),
            ('microbiology', 'Microbiologie')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_analysis_type'
        }),
        label="Type d'analyse"
    )

    sample_type = forms.ChoiceField(
        choices=[
            ('', 'Tous les types'),
            ('blood', 'Sang'),
            ('urine', 'Urine'),
            ('tissue', 'Tissu')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_sample_type'
        }),
        label="Type d'échantillon"
    )

    activity_description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'id': 'id_activity_description'
        }),
        label="Description de l'activité"
    )

    performance_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'id': 'id_performance_notes'
        }),
        label="Notes de performance"
    )

    generated_by = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_generated_by'
        }),
        label="Généré par"
    )

    include_details = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_include_details'
        }),
        label="Inclure les détails complets"
    )

    group_by_department = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_group_by_department'
        }),
        label="Grouper par département"
    )

    class Meta:
        model = Report
        fields = [
            'report_type',
            'format',
            'start_date',
            'end_date',
            'generated_by',
            'include_details',
            'group_by_department'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')

        # Initialize results queryset based on dates if they exist in POST data
        if 'start_date' in self.data and 'end_date' in self.data:
            try:
                start_date = self.data['start_date']
                end_date = self.data['end_date']
                self.fields['results'].queryset = self._get_filtered_results(start_date, end_date)
            except (ValueError, TypeError):
                pass  # Invalid date format, use default empty queryset

        # For existing reports, initialize with previous selection
        elif instance and instance.pk and instance.start_date and instance.end_date:
            self.fields['results'].queryset = self._get_filtered_results(
                instance.start_date,
                instance.end_date
            )
            if 'selected_results' in instance.parameters:
                self.fields['results'].initial = instance.parameters['selected_results']

        # Set required fields based on report type
        if 'report_type' in self.data:
            report_type = self.data['report_type']
            if report_type == 'activity':
                self.fields['activity_description'].required = True
            elif report_type == 'performance':
                self.fields['performance_notes'].required = True

    def _get_filtered_results(self, start_date, end_date):
        """Helper method to get filtered results queryset"""
        return Result.objects.filter(
            test_date__date__range=[start_date, end_date],
            status='completed'
        ).select_related(
            'sample',
            'sample__patient'
        ).order_by('-test_date')

    def clean(self):
        cleaned_data = super().clean()
        report_type = cleaned_data.get('report_type')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        # Validate date range
        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError("La date de fin doit être postérieure à la date de début")
            if start_date > timezone.now().date():
                raise ValidationError("La date de début ne peut pas être dans le futur")
            if end_date > timezone.now().date():
                raise ValidationError("La date de fin ne peut pas être dans le futur")

        # Validate report type specific requirements
        if report_type == 'results':
            if not cleaned_data.get('results'):
                raise ValidationError("Vous devez sélectionner au moins un résultat pour un rapport de résultats")
        elif report_type == 'activity':
            if not cleaned_data.get('activity_description'):
                raise ValidationError("Une description de l'activité est requise")
        elif report_type == 'performance':
            if not cleaned_data.get('performance_notes'):
                raise ValidationError("Des notes de performance sont requises")

        return cleaned_data

    def save(self, commit=True):
        report = super().save(commit=False)

        # Prepare parameters data
        report.parameters = {
            'report_type': self.cleaned_data['report_type'],
            'generated_by': self.cleaned_data['generated_by'],
            'start_date': self.cleaned_data['start_date'].strftime('%Y-%m-%d'),
            'end_date': self.cleaned_data['end_date'].strftime('%Y-%m-%d'),
            'include_details': self.cleaned_data.get('include_details', False),
            'group_by_department': self.cleaned_data.get('group_by_department', False)
        }

        # Add type-specific parameters
        if report.report_type == 'results':
            selected_results = self.cleaned_data.get('results', [])
            report.parameters.update({
                'analysis_type': self.cleaned_data.get('analysis_type'),
                'sample_type': self.cleaned_data.get('sample_type'),
                'selected_results': [result.id for result in selected_results],
                'results_count': len(selected_results)
            })
        elif report.report_type == 'activity':
            report.parameters['description'] = self.cleaned_data.get('activity_description', '')
        elif report.report_type == 'performance':
            report.parameters['notes'] = self.cleaned_data.get('performance_notes', '')

        if commit:
            report.save()

        return report