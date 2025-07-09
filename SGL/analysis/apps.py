# analysis/apps.py
from django.apps import AppConfig


class AnalysisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analysis'

    def ready(self):
        """
        Override this method to perform initialization tasks including:
        - Importing and connecting signals
        - Running startup code
        """
        # Import signals module to register signal handlers
        from . import signals  # noqa

        # Optional: You can also connect signals directly here if preferred
        # from django.db.models.signals import post_save
        # from equipment.models import EquipmentResult
        # from .signals import process_equipment_result
        # post_save.connect(process_equipment_result, sender=EquipmentResult)