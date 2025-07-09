from django.contrib import admin
from .models import Bill

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'amount', 'status', 'issued_date')
    list_filter = ('status',)
    search_fields = ('patient__first_name', 'patient__last_name')
    raw_id_fields = ('patient',)