# reports/tasks.py
from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone

from reports.utils import generate_pdf_report
from doctors.models import Doctor


@shared_task
def send_daily_reports():
    doctors = Doctor.objects.all()
    for doctor in doctors:
        # Generate PDF
        pdf_content = generate_pdf_report({
            'doctor': doctor,
            'samples': doctor.samples_referred.all()
        })

        # Send Email
        email = EmailMessage(
            subject=f"Daily Lab Report - {timezone.now().date()}",
            body="Attached is your daily report.",
            to=[doctor.email],
            attachments=[('report.pdf', pdf_content, 'application/pdf')]
        )
        email.send()