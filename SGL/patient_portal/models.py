from django.contrib.auth.models import AbstractUser
from django.db import models

class PatientUser(AbstractUser):
    pass
    class Meta:
        permissions = [
            ("can_view_portal", "Can access patient portal"),
        ]

    # Add custom related_names to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="patient_user_groups",  # Unique name
        related_query_name="patient_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="patient_user_permissions",  # Unique name
        related_query_name="patient_user",
    )

    def __str__(self):
        if hasattr(self, 'patient_profile'):
            return f"Portal User: {self.patient_profile.full_name}"
        return f"Portal User: {self.username}"