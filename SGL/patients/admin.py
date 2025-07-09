from django.contrib import admin
from .models import Patient
from import_export import resources
from import_export.admin import ImportExportModelAdmin


class PatientResource(resources.ModelResource):
    class Meta:
        model = Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'date_of_birth', 'gender', 'phone_number')
    list_filter = ('gender',)
    search_fields = ('first_name', 'last_name', 'phone_number')
    readonly_fields = ('qr_code',)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:  # Only for new patients
            bill = obj.generate_bill()
            from billing.utils import generate_bill_pdf
            generate_bill_pdf(bill)