from django.contrib import admin
from .models import SampleType, Sample

@admin.register(SampleType)
class SampleTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'processing_days')
    search_fields = ('name',)

@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'patient', 'sample_type', 'status', 'collection_date')
    list_filter = ('status', 'sample_type')
    search_fields = ('barcode', 'patient__first_name', 'patient__last_name')
    raw_id_fields = ('patient',)
    date_hierarchy = 'collection_date'