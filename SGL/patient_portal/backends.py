from django.contrib.auth import get_user_model

class PatientAuthBackend:
    def authenticate(self, request, username=None, password=None):
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
            if hasattr(user, 'patient_profile') and user.check_password(password):
                return user
            return None  # Explicitly return None if auth fails
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):  # Add this required method
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None