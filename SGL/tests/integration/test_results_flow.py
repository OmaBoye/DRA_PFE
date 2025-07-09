# tests/integration/test_results_flow.py
from unittest.mock import patch

from django.test import TestCase
from tests.factories import AnalysisFactory
from tests.mocks.blood_analyzer import get_success_response


class TestAutoResultsGeneration(TestCase):
    def test_full_workflow(self):
        # 1. Create analysis
        analysis = AnalysisFactory(status='pending')

        # 2. Mock equipment response
        with patch('equipment.connectors.EquipmentConnector.poll_results',
                   return_value=[get_success_response()]):
            # 3. Trigger result generation
            from equipment.management.commands import poll_results
            cmd = poll_results.Command()
            cmd.handle()

            # 4. Verify
            result = analysis.sample.result
            self.assertEqual(result.values['hemoglobin'], '14.2 g/dL')
            self.assertEqual(analysis.status, 'completed')