from django.contrib import admin
from .models import Result

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('sample', 'patient', 'status', 'test_date')
    list_filter = ('status',)
    search_fields = ('sample__barcode', 'sample__patient__first_name', 'sample__patient__last_name')
    raw_id_fields = ('sample',)
    date_hierarchy = 'test_date'

    def patient(self, obj):
        return obj.sample.patient
    patient.short_description = 'Patient'