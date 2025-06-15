from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from openpyxl import Workbook
from django.http import HttpResponse


def generate_pdf_report(data, title):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # PDF Content
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, title)
    p.setFont("Helvetica", 12)

    y = 700
    for item in data:
        p.drawString(100, y, f"• {str(item)}")
        y -= 20

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer


def generate_excel_report(data, title):
    buffer = BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = title[:30]  # Excel sheet name limit

    # Excel Content
    ws.append(["ID", "Details"])  # Headers
    for item in data:
        ws.append([item.id, str(item)])

    wb.save(buffer)
    buffer.seek(0)
    return buffer