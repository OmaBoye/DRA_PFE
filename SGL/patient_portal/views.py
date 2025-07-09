from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.utils import timezone
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib import messages
from django.urls import reverse
import logging

from patients.models import Patient
from analysis.models import Analysis
from results.models import Result

logger = logging.getLogger(__name__)


class PatientResultsPortalView(TemplateView):
    """
    Main portal view for patients to access their test results
    Secure access via QR token validation
    """
    template_name = "patient_portal/patient_results_portal.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token = kwargs.get('token')

        if not token:
            logger.error("No token provided in URL")
            raise Http404("Access token required")

        try:
            patient = get_object_or_404(Patient, qr_token=token)

            if patient.qr_token_expires < timezone.now():
                logger.warning(f"Expired token attempt: {token}")
                raise Http404("QR code expired - please request a new one")

            context.update({
                'patient': patient,
                'pending_analyses': Analysis.objects.filter(
                    sample__patient=patient,
                    status__in=['pending', 'in_progress']
                ).select_related('sample', 'analysis_type'),

                'completed_results': Result.objects.filter(
                    sample__patient=patient,
                    status='completed'
                ).select_related('sample'),
                'token': token  # Pass token to template for print links
            })
            return context

        except Exception as e:
            logger.error(f"Portal view error: {str(e)}")
            raise Http404("Unable to load results")


def print_patient_result(request, token, result_id):
    """
    Secure PDF printing endpoint with proper error handling
    """
    try:
        # 1. Validate token and patient
        patient = get_object_or_404(Patient, qr_token=token)
        if patient.qr_token_expires < timezone.now():
            messages.error(request, "QR code expired")
            raise Http404("Expired token")

        # 2. Verify result belongs to patient
        result = get_object_or_404(
            Result,
            pk=result_id,
            sample__patient=patient,
            status='completed'
        )

        # 3. Safely get analysis type name
        analysis_name = "Unknown Test"
        if hasattr(result.sample, 'analysis_type'):
            analysis_name = result.sample.analysis_type.name
        elif hasattr(result.sample, 'analysis'):
            analysis_name = result.sample.analysis.analysis_type.name

        # 4. Generate PDF
        from io import BytesIO
        from reportlab.pdfgen import canvas

        buffer = BytesIO()
        p = canvas.Canvas(buffer)

        # PDF Content
        p.setFont("Helvetica-Bold", 14)
        p.drawString(100, 800, f"Test Result for {patient.full_name}")
        p.setFont("Helvetica", 12)
        p.drawString(100, 775, f"Test Name: {analysis_name}")
        p.drawString(100, 750, f"Date: {result.test_date.strftime('%Y-%m-%d')}")

        # Add your actual result data here
        y_position = 725
        if hasattr(result, 'values'):
            for param, value in result.values.items():
                p.drawString(100, y_position, f"{param}: {value}")
                y_position -= 25

        p.showPage()
        p.save()

        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="result_{result_id}_{patient.last_name}.pdf"'
        )
        return response

    except Exception as e:
        logger.error(f"Print error for token {token}: {str(e)}", exc_info=True)
        raise Http404("Error generating report. Please contact support.")

class PatientPortalAPIView(TemplateView):
    """
    JSON API endpoint for external systems
    Same token validation as web portal
    """

    def get(self, request, *args, **kwargs):
        token = kwargs.get('token')

        try:
            patient = get_object_or_404(Patient, qr_token=token)

            if patient.qr_token_expires < timezone.now():
                return JsonResponse(
                    {'error': 'Token expired'},
                    status=400
                )

            results = Result.objects.filter(
                sample__patient=patient,
                status='completed'
            ).select_related('sample')

            data = {
                'patient': {
                    'name': patient.full_name,
                    'dob': patient.date_of_birth.strftime('%Y-%m-%d')
                },
                'results': [
                    {
                        'id': r.id,
                        'test': r.sample.analysis_type.name,
                        'date': r.test_date.strftime('%Y-%m-%d'),
                        'pdf_url': reverse(
                            'patient_portal:print_result',
                            kwargs={
                                'token': token,
                                'result_id': r.id
                            }
                        )
                    } for r in results
                ]
            }
            return JsonResponse(data)

        except Exception as e:
            logger.error(f"API error: {str(e)}")
            return JsonResponse(
                {'error': 'Invalid request'},
                status=400
            )