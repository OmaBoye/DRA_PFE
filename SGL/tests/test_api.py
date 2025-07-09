# tests/test_api.py
from rest_framework.test import APITestCase

from results.models import Result


class ResultsWebhookTest(APITestCase):
    def test_webhook_creates_result(self):
        sample = ...  # Create sample fixture
        url = '/api/ehr/webhook/'
        data = {
            'sample_id': sample.barcode,
            'values': {'glucose': '95 mg/dL'}
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Result.objects.exists())