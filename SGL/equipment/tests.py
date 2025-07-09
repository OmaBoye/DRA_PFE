# equipment/tests.py
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from analysis.models import Analysis, AnalysisResult, AnalysisType
from samples.models import Sample
from patients.models import Patient
from equipment.models import LaboratoryEquipment, EquipmentTestRequest, EquipmentResult

User = get_user_model()


@override_settings(DEBUG=True)
class AutoResultsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com"
        )
        cls.patient = Patient.objects.create(
            first_name="Test",
            last_name="Patient",
            date_of_birth="2000-01-01"
        )
        cls.sample = Sample.objects.create(
            barcode="TEST123",
            patient=cls.patient,
            collection_date=timezone.now()
        )
        cls.analysis_type = AnalysisType.objects.create(
            name="Complete Blood Count",
            code="CBC",
            category="blood",
            is_auto_verifiable=False
        )
        cls.equipment = LaboratoryEquipment.objects.create(
            name="Hematology Analyzer",
            model="X200",
            ip_address="127.0.0.1",
            protocol="REST",
            is_active=True
        )

    def setUp(self):
        self.analysis = Analysis.objects.create(
            sample=self.sample,
            analysis_type=self.analysis_type,
            status="pending",
            created_by=self.user,
            instrument_used=self.equipment.name
        )

    @patch('requests.post')
    @patch('requests.get')
    @patch('analysis.services.generate_result_pdf')
    def test_full_workflow(self, mock_pdf, mock_get, mock_post):
        """Test complete workflow including PDF generation"""
        # Setup mocks
        mock_post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"status": "accepted"})
        )
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value=[{
                "sample_id": "TEST123",
                "values": {"WBC": 7.5, "HGB": 14.2}
            }])
        )
        mock_pdf.return_value = HttpResponse(status=200)

        # Execute workflow
        from equipment.connectors import EquipmentConnector
        connector = EquipmentConnector(self.equipment.id)
        connector.send_request(self.analysis.id)
        results = connector.poll_results()

        # Create EquipmentResult to trigger signal
        EquipmentTestRequest.objects.create(
            analysis=self.analysis,
            equipment=self.equipment,
            status="processed"
        )
        EquipmentResult.objects.create(
            test_request=EquipmentTestRequest.objects.first(),
            raw_data=results[0]
        )

        # Verify results
        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, "pending")

        # Verify AnalysisResult was created
        self.assertTrue(AnalysisResult.objects.filter(analysis=self.analysis).exists())

        # Verify PDF generation was called
        mock_pdf.assert_called_once()

    def test_error_handling(self):
        with patch('equipment.connectors.EquipmentConnector.poll_results') as mock_poll:
            mock_poll.side_effect = Exception("Simulated error")
            from equipment.connectors import EquipmentConnector
            connector = EquipmentConnector(self.equipment.id)
            with self.assertRaises(Exception):
                connector.poll_results()

    def test_data_formatting(self):
        from analysis.utils import format_equipment_data
        test_data = {"WBC": 7.5, "HGB": 14.2}
        formatted = format_equipment_data(test_data)
        self.assertEqual(formatted["hematology"]["WBC"]["value"], 7.5)
        self.assertEqual(formatted["hematology"]["HGB"]["value"], 14.2)

    @patch('analysis.services.render_to_pdf')
    def test_pdf_generation(self, mock_render):
        from analysis.services import generate_result_pdf
        mock_render.return_value = b"PDF_CONTENT"
        result = AnalysisResult.objects.create(
            analysis=self.analysis,
            raw_data=json.dumps({"WBC": 7.5, "HGB": 14.2}),
            formatted_data={
                "hematology": {
                    "WBC": {"value": 7.5, "unit": "10^3/μL", "range": "4.0-11.0"},
                    "HGB": {"value": 14.2, "unit": "g/dL", "range": "12.0-16.0"}
                }
            },
            is_auto_generated=True
        )
        response = generate_result_pdf(result)
        self.assertEqual(response.status_code, 200)

from verify_julius import verify_julius_connection

class TestJuliusIntegration(TestCase):
    def test_julius_config(self):
        self.assertTrue(verify_julius_connection())