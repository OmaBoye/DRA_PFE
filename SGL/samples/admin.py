from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import SampleType, Sample, Bill


@admin.register(SampleType)
class SampleTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'processing_days')
    search_fields = ('name',)




@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'patient', 'display_sample_types', 'status', 'collection_date','view_analyses')
    list_filter = ('status',)
    search_fields = ('barcode', 'patient__first_name', 'patient__last_name')
    raw_id_fields = ('patient',)
    date_hierarchy = 'collection_date'
    filter_horizontal = ('sample_type',)  # Adds a better widget for many-to-many

    def display_sample_types(self, obj):
        """Custom method to display sample types as comma-separated list"""
        return ", ".join([st.name for st in obj.sample_type.all()])

    display_sample_types.short_description = 'Sample Types'
    def view_analyses(self, obj):
        url = reverse('admin:analysis_analysis_changelist') + f'?sample__id={obj.id}'
        return format_html('<a href="{}">Analyses</a>', url)

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('sample', 'issued_date', 'paid', 'amount')
    list_filter = ('paid',)
    search_fields = ('sample__barcode',)
    date_hierarchy = 'issued_date'