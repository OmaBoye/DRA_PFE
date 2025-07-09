# analysis/middleware.py
from django.http import HttpResponse
from xhtml2pdf import pisa

class PDFGenerationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, pisa.pisaError):
            return HttpResponse(
                "PDF generation failed. Please try again later.",
                status=500
            )
        return None