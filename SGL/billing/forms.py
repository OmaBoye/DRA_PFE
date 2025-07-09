from django import forms
from .models import Bill

class BillUpdateForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['amount', 'status', 'paid_date']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'paid_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                },
                format='%Y-%m-%d'
            ),
        }



class BillCreateForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['amount', 'status']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'required': 'required'
            })
        }