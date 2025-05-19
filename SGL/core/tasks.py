from celery import shared_task
from django.core.management import call_command
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from analytics.models import LabPerformance

@shared_task
def cleanup_old_records():
    call_command('cleanup_old_records', years=5)


@shared_task
def send_weekly_report():
    data = LabPerformance.objects.last_7_days()

    # Generate HTML report
    html_content = render_to_string('analytics/weekly_report.html', {
        'data': data
    })

    # Send email
    email = EmailMessage(
        subject="Rapport Hebdomadaire du Laboratoire",
        body=html_content,
        to=['director@lab.com']
    )
    email.content_subtype = "html"
    email.send()