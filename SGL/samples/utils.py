from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.conf import settings
import os


def generate_bill_pdf(context):
    template = get_template('samples/bill_template.html')
    html = template.render(context)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None


def save_bill_pdf(bill_instance, pdf_content):
    file_name = f"bill_{bill_instance.sample.barcode}.pdf"
    file_path = os.path.join(settings.MEDIA_ROOT, 'bills', file_name)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'wb') as f:
        f.write(pdf_content)

    bill_instance.pdf_file.name = f'bills/{file_name}'
    bill_instance.save()