from django.apps import AppConfig

class UsersConfig(AppConfig):  # Make sure this class name matches
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'