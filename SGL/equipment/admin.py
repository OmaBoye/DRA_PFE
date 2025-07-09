from django.contrib import admin
from .models import LaboratoryEquipment, EquipmentTestRequest, EquipmentResult

@admin.register(LaboratoryEquipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'model', 'protocol', 'is_active')

@admin.register(EquipmentTestRequest)
class TestRequestAdmin(admin.ModelAdmin):
    list_display = ('analysis', 'equipment', 'status', 'sent_at')

@admin.register(EquipmentResult)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('test_request', 'received_at', 'is_parsed')