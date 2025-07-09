from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from patients.models import Patient
from results.models import Result
import requests
import logging
from .auth import EHRTokenAuth


logger = logging.getLogger(__name__)

class EHRPatientAPI(APIView):
    """Fetch patient data from hospital EHR."""
    def get(self, request):
        patient_id = request.GET.get('patient_id')
        try:
            patient = Patient.objects.get(id=patient_id)
            # Simulate EHR API call (replace with actual hospital API)
            ehr_response = requests.get(
                'https://hospital-ehr-api/patients',
                params={'id': patient_id},
                headers={'Authorization': 'Bearer YOUR_EHR_TOKEN'}
            )
            return Response(ehr_response.json())
        except Exception as e:
            logger.error(f"EHR fetch failed: {str(e)}")
            return Response({'error': 'Not found'}, status=404)

class EHRResultsWebhook(APIView):
    """Receive lab results from EHR."""
    def post(self, request):
        try:
            result_data = request.data
            Result.objects.create(
                sample_id=result_data['sample_id'],
                values=result_data['values'],
                status='completed'
            )
            return Response({'status': 'success'})
        except Exception as e:
            logger.error(f"Webhook failed: {str(e)}")
            return Response({'error': str(e)}, status=400)


class EHRResultsWebhook(APIView):
    permission_classes = [EHRTokenAuth]