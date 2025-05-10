from django.views.generic import ListView, CreateView, DetailView, TemplateView
from django.urls import reverse_lazy
from .models import Report
from .forms import ReportForm
from .utils import generate_pdf_report, generate_excel_report
from django.http import HttpResponse
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from openpyxl import Workbook


class ReportListView(ListView):
    model = Report
    template_name = 'reports/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().select_related('result__sample__patient')


class ReportCreateView(CreateView):
    model = Report
    form_class = ReportForm
    template_name = 'reports/report_form.html'
    success_url = reverse_lazy('reports:list')


class ReportDetailView(DetailView):
    model = Report
    template_name = 'reports/report_detail.html'
    context_object_name = 'report'


class ReportGenerateView(TemplateView):
    template_name = 'reports/report_form.html'

    def post(self, request, *args, **kwargs):
        report_type = request.POST.get('report_type')
        reports = Report.objects.all()  # Filter as needed

        if report_type == 'pdf':
            buffer = generate_pdf_report(reports, "Lab Reports")
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="reports.pdf"'
            return response

        elif report_type == 'excel':
            buffer = generate_excel_report(reports, "Lab Reports")
            response = HttpResponse(buffer,
                                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="reports.xlsx"'
            return response

        return super().get(request, *args, **kwargs)




def export_pdf(request, pk):
    report = Report.objects.get(pk=pk)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report_{pk}.pdf"'

    p = canvas.Canvas(response)
    p.drawString(100, 800, f"Report for {report.patient}")
    p.showPage()
    p.save()
    return response


def export_excel(request):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="reports.xlsx"'

    wb = Workbook()
    ws = wb.active
    ws.append(["Patient", "Sample", "Status"])

    for report in Report.objects.all():
        ws.append([report.patient, report.sample, report.status])

    wb.save(response)
    return response