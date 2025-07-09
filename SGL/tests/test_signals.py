# tests/test_signals.py
from django.test import TestCase
from analysis.models import Analysis
from results.models import Result


class SignalTests(TestCase):
    def test_auto_verification(self):
        analysis = Analysis.objects.create(
            status='completed',
            analysis_type__is_auto_verifiable=True,
            sample__patient=...  # Create fixtures
        )

        # Signal should create result automatically
        result = Result.objects.get(sample=analysis.sample)
        self.assertEqual(result.status, 'completed')