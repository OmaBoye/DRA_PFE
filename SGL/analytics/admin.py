from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from analytics.models import LabPerformance


class LabPerformanceResource(resources.ModelResource):
    class Meta:
        model = LabPerformance
        fields = ('date', 'samples_processed', 'avg_processing_time', 'critical_results')

@admin.register(LabPerformance)
class LabPerformanceAdmin(ImportExportModelAdmin):
    resource_class = LabPerformanceResource
    list_display = ('date', 'samples_processed', 'avg_processing_time')
    ordering = ('-date',)

