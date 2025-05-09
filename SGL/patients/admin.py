from django.contrib import admin
from .models import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'date_of_birth', 'gender', 'phone_number')
    list_filter = ('gender',)
    search_fields = ('first_name', 'last_name', 'phone_number')
    readonly_fields = ('qr_code',)