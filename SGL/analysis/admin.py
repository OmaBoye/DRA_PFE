from django.contrib import admin
from .models import AnalysisType, Analysis

@admin.register(AnalysisType)
class AnalysisTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    filter_horizontal = ('sample_types',)
    search_fields = ('name',)

@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ('sample', 'analysis_type', 'status', 'started_at', 'technician')
    list_filter = ('status', 'analysis_type')
    search_fields = ('sample__barcode', 'technician')
    raw_id_fields = ('sample',)
    date_hierarchy = 'created_at'