# patient_portal/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import PatientUser



# admin.py
class PatientUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'has_patient_profile')
    def has_patient_profile(self, obj):
        return hasattr(obj, 'patient_profile')
admin.site.register(PatientUser, PatientUserAdmin)
