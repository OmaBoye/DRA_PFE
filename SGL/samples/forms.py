from django import forms
from django.utils import timezone
from .models import Sample, SampleType
from patients.models import Patient


class SampleForm(forms.ModelForm):
    # Custom fields
    collector = forms.CharField(
        label="Préleveur",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    storage_temp = forms.ChoiceField(
        label="Température de stockage",
        choices=[
            ('', "Sélectionner..."),
            ('ambient', 'Ambiente'),
            ('refrigerated', 'Réfrigéré (2-8°C)'),
            ('frozen', 'Congelé (-20°C)')
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    collection_site = forms.CharField(
        label="Site de prélèvement",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    sample_type = forms.MultipleChoiceField(
        label="Type(s) d'échantillon",
        choices=[
            ('blood', 'Sang'),
            ('urine', 'Urine'),
            ('tissue', 'Tissu'),
            ('saliva', 'Salive')
        ],
        required=True,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Sample
        fields = ['patient', 'collection_date', 'barcode', 'notes']
        widgets = {
            'patient': forms.Select(attrs={
                'class': 'form-control',
                'required': 'required'
            }),
            'collection_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'required': 'required'
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control',
                'required': 'required'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set initial values
        self.fields['collection_date'].initial = timezone.now()

        # Customize patient dropdown
        self.fields['patient'].queryset = Patient.objects.all().order_by('last_name')
        self.fields['patient'].label_from_instance = lambda obj: (
            f"{obj.last_name}, {obj.first_name} ({obj.date_of_birth.strftime('%d/%m/%Y')})"
        )

        # Set initial value for sample_type if editing existing sample
        if self.instance and self.instance.pk:
            self.fields['sample_type'].initial = [
                st.name.lower()
                for st in self.instance.sample_type.all()
            ]

    def save(self, commit=True):
        # Handle sample_type separately since it's not using the direct FK
        sample = super().save(commit=False)

        if commit:
            sample.save()

        # Handle the many-to-many relationship
        sample_types = []
        for sample_type_name in self.cleaned_data['sample_type']:
            st, _ = SampleType.objects.get_or_create(
                name=sample_type_name.capitalize(),
                defaults={'processing_days': 1}
            )
            sample_types.append(st)

        sample.sample_type.set(sample_types)  # Set all selected types

        if commit:
            self.save_m2m()

        return sample