from django.contrib import admin
from .models import SampleType, Sample, Bill


@admin.register(SampleType)
class SampleTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'processing_days')
    search_fields = ('name',)


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'patient', 'display_sample_types', 'status', 'collection_date')
    list_filter = ('status',)
    search_fields = ('barcode', 'patient__first_name', 'patient__last_name')
    raw_id_fields = ('patient',)
    date_hierarchy = 'collection_date'
    filter_horizontal = ('sample_type',)  # Adds a better widget for many-to-many

    def display_sample_types(self, obj):
        """Custom method to display sample types as comma-separated list"""
        return ", ".join([st.name for st in obj.sample_type.all()])

    display_sample_types.short_description = 'Sample Types'

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('sample', 'issued_date', 'paid', 'amount')
    list_filter = ('paid',)
    search_fields = ('sample__barcode',)
    date_hierarchy = 'issued_date'