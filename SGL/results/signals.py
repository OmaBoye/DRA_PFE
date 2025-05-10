from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Result

@receiver(post_save, sender=Result)
def send_result_email(sender, instance, created, **kwargs):
    if instance.status == 'completed':
        send_mail(
            'Your Lab Results Are Ready',
            f'Results for {instance.sample} are now available.',
            'noreply@lab.com',
            [instance.sample.patient.email],
            fail_silently=False,
        )