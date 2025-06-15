from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Administrator')
        BIOLOGIST = 'biologist', _('Biologist')
        TECHNICIAN = 'technician', _('Laboratory Technician')
        RECEPTIONIST = 'receptionist', _('Receptionist')
        PATIENT = 'patient', _('Patient')

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.TECHNICIAN,
        verbose_name=_('Role')
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Phone Number')
    )

    is_patient = models.BooleanField(
        default=False,
        verbose_name=_('Is Patient')
    )

    date_of_birth = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Date of Birth')
    )

    address = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Address')
    )

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['last_name', 'first_name']
        permissions = [
            ('can_view_dashboard', 'Can view dashboard'),
            ('can_manage_users', 'Can manage users'),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def clean(self):
        super().clean()
        # Ensure role and is_patient are consistent
        if self.role == self.Role.PATIENT and not self.is_patient:
            self.is_patient = True
        elif self.role != self.Role.PATIENT and self.is_patient:
            self.is_patient = False

    def save(self, *args, **kwargs):
        self.clean()  # Run validation before saving

        # Set username to email if not provided
        if not self.username and self.email:
            self.username = self.email

        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return self.get_full_name()

    def log_activity(self, activity, details=None):
        """Helper method to log user activities"""
        return UserActivity.objects.create(
            user=self,
            activity=activity,
            details=details or {}
        )


class UserActivity(models.Model):
    class ActivityType(models.TextChoices):
        LOGIN = 'login', _('Login')
        LOGOUT = 'logout', _('Logout')
        PROFILE_UPDATE = 'profile_update', _('Profile Update')
        PASSWORD_CHANGE = 'password_change', _('Password Change')
        SYSTEM_ACTION = 'system_action', _('System Action')

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name=_('User')
    )

    activity = models.CharField(
        max_length=50,
        choices=ActivityType.choices,
        verbose_name=_('Activity Type')
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Timestamp')
    )

    details = models.JSONField(
        default=dict,
        verbose_name=_('Activity Details')
    )

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=_('IP Address')
    )

    user_agent = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('User Agent')
    )

    class Meta:
        verbose_name = _('User Activity')
        verbose_name_plural = _('User Activities')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['activity', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_activity_display()} at {self.timestamp}"


@receiver(post_save, sender=User)
def handle_user_save(sender, instance, created, **kwargs):
    if created:
        # Log account creation activity
        instance.log_activity(
            UserActivity.ActivityType.SYSTEM_ACTION,
            {'action': 'account_creation'}
        )

        # Set default permissions based on role
        if instance.role == User.Role.ADMIN:
            instance.is_staff = True
            instance.save()