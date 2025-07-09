from django.views.generic import ListView, CreateView, DetailView, TemplateView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas
from openpyxl import Workbook
from .models import Report
from .forms import ReportForm
from .utils import generate_pdf_report, generate_excel_report
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from results.models import Result


class ReportListView(ListView):
    model = Report
    template_name = 'reports/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        report_type = self.request.GET.get('type')
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        return queryset.order_by('-created_at')


class ReportDetailView(DetailView):
    model = Report
    template_name = 'reports/report_detail.html'
    context_object_name = 'report'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.object

        # Get selected results for this report
        if report.report_type == 'results' and 'selected_results' in report.parameters:
            result_ids = report.parameters['selected_results']
            context['results'] = Result.objects.filter(
                id__in=result_ids
            ).select_related(
                'sample',
                'sample__patient'
            ).order_by('-test_date')

        return context


class ReportGenerateView(TemplateView):
    template_name = 'reports/report_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ReportForm()
        return context

    def _prepare_report_data(self, form, report_type):
        """Prepare the data dictionary based on report type"""
        data = {
            'report_type': report_type,
            'generated_by': form.cleaned_data['generated_by'],
            'start_date': form.cleaned_data['start_date'].strftime('%Y-%m-%d'),
            'end_date': form.cleaned_data['end_date'].strftime('%Y-%m-%d'),
            'include_details': form.cleaned_data.get('include_details', False),
            'group_by_department': form.cleaned_data.get('group_by_department', False)
        }

        if report_type == 'results':
            selected_results = form.cleaned_data.get('results', [])
            data.update({
                'analysis_type': form.cleaned_data.get('analysis_type'),
                'sample_type': form.cleaned_data.get('sample_type'),
                'selected_results': [result.id for result in selected_results],
                'results_count': len(selected_results),
                'results_data': [{
                    'id': r.id,
                    'barcode': r.sample.barcode,
                    'patient': str(r.sample.patient),
                    'test_type': r.test_type.name if hasattr(r, 'test_type') else 'N/A',
                    'status': r.get_status_display(),
                    'date': r.test_date.strftime('%Y-%m-%d')
                } for r in selected_results]
            })
        elif report_type == 'activity':
            data['description'] = form.cleaned_data.get('activity_description', '')
        elif report_type == 'performance':
            data['notes'] = form.cleaned_data.get('performance_notes', '')

        return data

    def post(self, request, *args, **kwargs):
        form = ReportForm(request.POST)
        if not form.is_valid():
            return self.render_to_response({'form': form})

        report_type = form.cleaned_data['report_type']

        # Validate that at least one result is selected for results reports
        if report_type == 'results' and not form.cleaned_data.get('results'):
            form.add_error(None, "Vous devez sélectionner au moins un résultat")
            return self.render_to_response({'form': form})

        data = self._prepare_report_data(form, report_type)

        # Create report first without file
        report = Report.objects.create(
            generated_by=form.cleaned_data['generated_by'],
            report_type=report_type,
            start_date=form.cleaned_data['start_date'],
            end_date=form.cleaned_data['end_date'],
            format=form.cleaned_data['format'],
            parameters=data
        )

        try:
            # Generate and save the file
            if form.cleaned_data['format'] == 'pdf':
                buffer = generate_pdf_report(data, f"{report_type}_report")
                report.file.save(f'report_{report.id}.pdf', ContentFile(buffer))
            elif form.cleaned_data['format'] == 'excel':
                buffer = generate_excel_report(data, f"{report_type}_report")
                report.file.save(f'report_{report.id}.xlsx', ContentFile(buffer))
            else:  # CSV
                buffer = generate_excel_report(data, f"{report_type}_report")
                report.file.save(f'report_{report.id}.csv', ContentFile(buffer))

            report.save()
            return redirect('reports:detail', pk=report.id)
        except Exception as e:
            # Handle file generation errors
            report.delete()  # Remove the report if file generation fails
            form.add_error(None, f"Failed to generate report: {str(e)}")
            return self.render_to_response({'form': form})


class ReportDeleteView(DeleteView):
    model = Report
    success_url = reverse_lazy('reports:list')

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


class ResultsAPIView(APIView):
    """API endpoint for fetching results based on date range"""

    def get(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        analysis_type = request.GET.get('analysis_type')

        results = Result.objects.filter(status='completed').select_related('sample', 'sample__patient')

        if start_date and end_date:
            results = results.filter(
                test_date__date__range=[start_date, end_date]
            )

        if analysis_type:
            # Update this filter based on your actual model structure
            results = results.filter(sample__analysis_type=analysis_type)

        data = [{
            'id': r.id,
            'barcode': r.sample.barcode,
            'patient': str(r.sample.patient),
            'test_type': r.sample.analysis_type if hasattr(r.sample, 'analysis_type') else 'N/A',
            'status': r.get_status_display(),
            'date': r.test_date.strftime('%Y-%m-%d')
        } for r in results]

        return Response(data)

def export_pdf(request, pk):
    report = Report.objects.get(pk=pk)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report_{pk}.pdf"'

    p = canvas.Canvas(response)
    p.drawString(100, 800, f"Report for {report.generated_by}")
    p.drawString(100, 780, f"Type: {report.get_report_type_display()}")
    p.drawString(100, 760, f"Period: {report.start_date} to {report.end_date}")
    p.showPage()
    p.save()
    return response


def export_excel(request, pk):
    report = Report.objects.get(pk=pk)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="report_{pk}.xlsx"'

    wb = Workbook()
    ws = wb.active
    ws.title = "Report Data"

    # Headers
    ws.append(["Field", "Value"])
    ws.append(["Generated By", report.generated_by])
    ws.append(["Report Type", report.get_report_type_display()])
    ws.append(["Start Date", report.start_date])
    ws.append(["End Date", report.end_date])

    wb.save(response)
    return response


class ResultsAPIView(APIView):
    def get(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        results = Result.objects.all()
        if start_date and end_date:
            results = results.filter(
                created_at__range=[start_date, end_date]
            )

        data = [{
            'id': r.id,
            'display_text': f"{r.sample.barcode} - {r.test_type}"  # Adjust as needed
        } for r in results]

        return Response(data)