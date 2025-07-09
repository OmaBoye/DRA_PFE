from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings


class DashboardViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create test data here if needed
        pass

    def setUp(self):
        self.client = Client()
        self.url = reverse('core:dashboard')  # Make sure this matches your URL name

    def test_dashboard_counts(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Add assertions for your counts
        # self.assertContains(response, "3 patients") etc.