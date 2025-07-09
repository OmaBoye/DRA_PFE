from django.contrib import admin
from django.utils.html import format_html

from .models import AnalysisType, Analysis, AnalysisResult


@admin.register(AnalysisType)
class AnalysisTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    filter_horizontal = ('sample_types',)
    search_fields = ('name',)

@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ('sample', 'status', 'started_at', 'technician')
    list_filter = ('status',)
    search_fields = ('sample__barcode', 'technician')
    raw_id_fields = ('sample',)
    date_hierarchy = 'created_at'


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('analysis', 'is_auto_generated', 'is_approved', 'created_at')
    list_filter = ('is_auto_generated', 'is_approved')
    readonly_fields = ('raw_data_preview',)

    def raw_data_preview(self, obj):
        return format_html('<pre>{}</pre>', json.dumps(obj.raw_data, indent=2))