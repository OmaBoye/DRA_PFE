# patient_portal/middleware.py

import re
import logging
from django.http import HttpResponseForbidden
from django.utils import timezone
from patients.models import Patient

logger = logging.getLogger(__name__)

class PortalAccessMiddleware:
    """
    Middleware to validate QR token access to the patient portal.
    Applies only to /portal/ URLs.
    Extracts token from the URL path or GET parameters.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Pattern matches /portal/results/<token>/ or /portal/print/<token>/<id>/ or /portal/api/<token>/
        self.token_pattern = re.compile(
            r'^/portal/(?:(?:results|print|api)/)(?P<token>[a-zA-Z0-9\-]+)/?'
        )

    def __call__(self, request):
        # Skip for non-portal paths
        if not request.path.startswith('/portal/'):
            return self.get_response(request)

        token = None

        # Try to extract token from path using regex
        match = self.token_pattern.match(request.path)
        if match:
            token = match.group('token')

        # Fallback to query string or session
        token = token or request.GET.get('token') or request.session.get('portal_token')

        if not token:
            logger.warning("Access denied: No token provided")
            return HttpResponseForbidden("Access token required")

        try:
            patient = Patient.objects.get(qr_token=token)

            if patient.qr_token_expires < timezone.now():
                logger.warning(f"Expired token used: {token}")
                return HttpResponseForbidden("Token expired")

            # Attach patient and token to request for view access
            request.patient = patient
            request.portal_token = token
            return self.get_response(request)

        except Patient.DoesNotExist:
            logger.warning(f"Invalid token: {token}")
            return HttpResponseForbidden("Invalid token")

        except Exception as e:
            logger.exception(f"Middleware error: {str(e)}")
            return HttpResponseForbidden("Server error")
