# analysis/services.py
from io import BytesIO
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import get_template
from django.templatetags.static import static
from xhtml2pdf import pisa


def render_to_pdf(template_name, context):
    template = get_template(template_name)
    html = template.render(context)
    result = BytesIO()

    pdf = pisa.pisaDocument(
        BytesIO(html.encode("UTF-8")),
        result,
        encoding="UTF-8"
    )

    if not pdf.err:
        return result.getvalue()
    return None


def generate_result_pdf(result):
    context = {
        'result': result,
        'now': timezone.now(),
        'logo_path': static('images/logo.png')  # Add your logo
    }
    pdf = render_to_pdf('analysis/result_pdf.html', context)

    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"LabResult_{result.analysis.sample.barcode}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return HttpResponse("PDF generation failed", status=500)
