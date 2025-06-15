from django.contrib import admin
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('result', 'patient', 'generated_by', 'created_at')
    search_fields = ('result__sample__barcode', 'generated_by', 'result__sample__patient__first_name')
    raw_id_fields = ('result',)
    date_hierarchy = 'created_at'

    def patient(self, obj):
        return obj.result.patient
    patient.short_description = 'Patient'