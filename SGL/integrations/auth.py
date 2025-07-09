from rest_framework.permissions import BasePermission

class EHRTokenAuth(BasePermission):
    """Validate EHR system tokens."""
    def has_permission(self, request, view):
        return request.headers.get('X-EHR-Token') == 'YOUR_SHARED_SECRET'