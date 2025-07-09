# tests/test_auto_results.py
from django.test import TestCase
from analysis.models import Analysis
from results.models import Result
from unittest.mock import patch

class AutoResultsTest(TestCase):
    def setUp(self):
        self.analysis = Analysis.objects.create(
            status='in_progress',
            sample=...  # Create sample fixture
        )

    @patch('equipment.connectors.EquipmentConnector.poll_results')
    def test_auto_result_creation(self, mock_poll):
        # Mock equipment returning fake results
        mock_poll.return_value = [{
            'sample_id': self.analysis.sample.barcode,
            'values': {'glucose': '95', 'hemoglobin': '14.2'},
            'timestamp': '2023-01-01T12:00:00'
        }]

        # Run the poll_results manaent command
        from django.core.management import call_command
        call_command('poll_results')

        # Verify result was created
        result = Result.objects.first()
        self.assertEqual(result.values['glucose'], '95')
        self.assertEqual(result.status, 'completed')