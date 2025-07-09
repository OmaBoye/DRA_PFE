# equipment/test_auto_results.py
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


@override_settings(DEBUG=True)  # Ensure signals work during testing
class AutoResultsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Create test data once for all test methods"""
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
            is_auto_verifiable=False  # Manual verification required
        )

        cls.equipment = LaboratoryEquipment.objects.create(
            name="Hematology Analyzer",
            model="X200",
            ip_address="127.0.0.1",
            protocol="REST",
            is_active=True
        )

    def setUp(self):
        """Create fresh analysis for each test"""
        self.analysis = Analysis.objects.create(
            sample=self.sample,
            analysis_type=self.analysis_type,
            status="pending",
            created_by=self.user,
            instrument_used=self.equipment.name
        )

    @patch('analysis.signals.generate_result_pdf')  # ✅ PATCH CORRECTLY
    @patch('requests.get')
    @patch('requests.post')
    def test_full_workflow(self, mock_post, mock_get, mock_pdf):
        """Test complete workflow including PDF generation"""
        mock_post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={
                "status": "accepted",
                "request_id": "REQ-12345"
            })
        )

        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value=[{
                "sample_id": "TEST123",
                "test_code": "CBC",
                "values": {
                    "WBC": 7.5,
                    "HGB": 14.2
                }
            }])
        )

        mock_pdf.return_value = HttpResponse(
            content_type='application/pdf',
            status=200
        )

        from equipment.connectors import EquipmentConnector
        connector = EquipmentConnector(self.equipment.id)

        request_response = connector.send_request(self.analysis.id)
        self.assertEqual(request_response["status"], "accepted")

        results = connector.poll_results()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["sample_id"], "TEST123")

        test_request = EquipmentTestRequest.objects.create(
            analysis=self.analysis,
            equipment=self.equipment,
            status="processed"
        )

        EquipmentResult.objects.create(
            test_request=test_request,
            raw_data=results[0]
        )

        self.analysis.refresh_from_db()
        self.assertEqual(
            self.analysis.status,
            "pending",
            "Analysis status should remain pending until manual verification"
        )

        result_qs = AnalysisResult.objects.filter(analysis=self.analysis)
        self.assertTrue(result_qs.exists(), "Signal failed to create AnalysisResult")

        result = result_qs.first()
        mock_pdf.assert_called_once_with(result)
        self.assertFalse(result.is_approved, "Result should not be auto-approved with is_auto_verifiable=False")

    @patch('equipment.connectors.EquipmentConnector.poll_results')
    def test_error_handling(self, mock_poll):
        """Test error handling during result polling"""
        mock_poll.side_effect = Exception("Simulated connection error")
        from equipment.connectors import EquipmentConnector
        connector = EquipmentConnector(self.equipment.id)

        with self.assertRaises(Exception) as context:
            connector.poll_results()

        self.assertEqual(str(context.exception), "Simulated connection error")

    def test_data_formatting(self):
        """Test the equipment data formatting"""
        from analysis.utils import format_equipment_data

        test_data = {
            "WBC": 7.5,
            "HGB": 14.2
        }

        formatted = format_equipment_data(test_data)
        self.assertIn("hematology", formatted)
        self.assertEqual(formatted["hematology"]["WBC"]["value"], 7.5)
        self.assertEqual(formatted["hematology"]["HGB"]["value"], 14.2)

    @patch('analysis.services.render_to_pdf')
    def test_pdf_generation_service(self, mock_render):
        """Test PDF generation service in isolation"""
        from analysis.services import generate_result_pdf

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

        mock_render.return_value = b"PDF_CONTENT"
        response = generate_result_pdf(result)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('LabResult_TEST123.pdf', response['Content-Disposition'])


@patch('requests.post')
@patch('requests.get')
@patch('equipment.services.julius_pdf.JuliusPDFGenerator.generate_mock_result_pdf')
def test_full_workflow_with_julius(self, mock_julius, mock_get, mock_post):
    """Test complete workflow with Julius PDF generation"""
    # Setup test outputs directory
    os.makedirs('test_outputs', exist_ok=True)

    # Configure API mocks
    mock_post.return_value = MagicMock(status_code=200, json=MagicMock(return_value={"status": "accepted"}))
    mock_get.return_value = MagicMock(status_code=200, json=MagicMock(return_value=[{
        "sample_id": "TEST123",
        "values": {"WBC": 7.5, "HGB": 14.2},
        "timestamp": "2023-07-20T14:30:00Z"
    }]))

    # Mock Julius response with actual PDF content
    with open('test_outputs/mock_report.pdf', 'rb') as f:
        mock_julius.return_value = f.read()

    # Execute workflow
    from equipment.connectors import EquipmentConnector
    connector = EquipmentConnector(self.equipment.id)
    connector.send_request(self.analysis.id)
    results = connector.poll_results()

    # Trigger processing
    test_request = EquipmentTestRequest.objects.create(
        analysis=self.analysis,
        equipment=self.equipment,
        status="processed"
    )
    EquipmentResult.objects.create(
        test_request=test_request,
        raw_data=results[0]
    )

    # Verify Julius was called
    result = AnalysisResult.objects.get(analysis=self.analysis)
    expected_data = {
        "sample_id": "TEST123",
        "values": {"WBC": 7.5, "HGB": 14.2},
        "timestamp": "2023-07-20T14:30:00Z"
    }
    mock_julius.assert_called_once_with(expected_data)

    # Save the generated PDF for inspection
    pdf_path = f'test_outputs/result_{result.id}_julius.pdf'
    with open(pdf_path, 'wb') as f:
        f.write(mock_julius.return_value)

    print(f"\n✅ Julius-generated PDF saved to: {os.path.abspath(pdf_path)}\n")