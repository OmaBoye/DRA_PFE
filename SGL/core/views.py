from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.utils import timezone
from django.db.models import Count, Sum, Avg
from datetime import timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
import logging
import json
from pyzbar.pyzbar import decode
from PIL import Image
from io import BytesIO
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.conf import settings
import os

from patients.models import Patient
from samples.models import Sample
from analysis.models import Analysis
from results.models import Result
from analytics.models import LabPerformance
from billing.models import Bill

logger = logging.getLogger(__name__)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        print("\nACTUAL DATABASE COUNTS:")
        print("Patients:", Patient.objects.count())
        print("Samples:", Sample.objects.count())
        print("Analyses:", Analysis.objects.count())
        print("Recent samples:", Sample.objects.order_by('-collection_date')[:5])

        try:
            # Basic counts
            context.update({
                'patient_count': Patient.objects.count(),
                'total_samples': Sample.objects.count(),
                'analysis_count': Analysis.objects.count(),
                'recent_samples': Sample.objects.select_related('patient').order_by('-collection_date')[:5],
            })

            # Fallback-safe critical results
            try:
                last_7_days = LabPerformance.objects.last_7_days()
            except AttributeError:
                print("Warning: LabPerformance.objects.last_7_days() not found. Using fallback.")
                seven_days_ago = timezone.now() - timedelta(days=7)
                last_7_days = LabPerformance.objects.filter(date__gte=seven_days_ago)

            context['critical_count'] = last_7_days.aggregate(
                total_critical=Sum('critical_results')
            )['total_critical'] or 0

            # Sample status chart data
            status_counts = Sample.objects.values('status').annotate(count=Count('id'))
            context['sample_status'] = {
                'labels': [s['status'] for s in status_counts],
                'data': [s['count'] for s in status_counts]
            }

            # Throughput data
            thirty_days_ago = timezone.now() - timedelta(days=30)
            date_range = [(timezone.now() - timedelta(days=x)).date() for x in range(30)][::-1]

            # Sample throughput
            samples = (
                Sample.objects
                .filter(collection_date__gte=thirty_days_ago)
                .extra({'day': "date(collection_date)"})
                .values('day')
                .annotate(count=Count('id'))
                .order_by('day')
            )
            samples_dict = {item['day']: item['count'] for item in samples}
            context['throughput_data'] = {
                'labels': [d.strftime('%Y-%m-%d') for d in date_range],
                'data': [samples_dict.get(d, 0) for d in date_range]
            }

            # Results throughput
            results = (
                Result.objects
                .filter(test_date__gte=thirty_days_ago)
                .extra({'day': "date(test_date)"})
                .values('day')
                .annotate(count=Count('id'))
                .order_by('day')
            )
            results_dict = {item['day']: item['count'] for item in results}
            context['results_data'] = {
                'labels': [d.strftime('%Y-%m-%d') for d in date_range],
                'data': [results_dict.get(d, 0) for d in date_range]
            }

            # Turnaround time
            try:
                turnaround = LabPerformance.objects.last_30_days()
            except AttributeError:
                print("Warning: LabPerformance.objects.last_30_days() not found. Using fallback.")
                turnaround = LabPerformance.objects.filter(date__gte=thirty_days_ago)

            turnaround_data = {
                'labels': [t.date.strftime('%Y-%m-%d') for t in turnaround],
                'data': [float(t.avg_processing_time) for t in turnaround]
            }
            context['turnaround_data'] = turnaround_data

            # Averages
            if turnaround_data['data']:
                context['avg_processing_time'] = sum(turnaround_data['data']) / len(turnaround_data['data'])
            else:
                context['avg_processing_time'] = 0

            avg_turnaround = turnaround.aggregate(
                avg_time=Avg('avg_processing_time')
            )['avg_time'] or 0
            context['avg_turnaround_30days'] = float(avg_turnaround)

            context['turnaround_percentage'] = min(100, (context['avg_processing_time'] / 24) * 100) if context[
                'avg_processing_time'] else 0

        except Exception as e:
            logger.error(f"Dashboard data error: {e}")
            print("Dashboard Exception:", e)

            # Safe fallback context
            context.update({
                'patient_count': 0,
                'total_samples': 0,
                'analysis_count': 0,
                'critical_count': 0,
                'recent_samples': [],
                'sample_status': {'labels': [], 'data': []},
                'throughput_data': {'labels': [], 'data': []},
                'results_data': {'labels': [], 'data': []},
                'turnaround_data': {'labels': [], 'data': []},
                'avg_processing_time': 0,
                'avg_turnaround_30days': 0,
                'turnaround_percentage': 0,
            })

        print("\nCONTEXT BEING SENT TO TEMPLATE:")
        print("patient_count:", context['patient_count'])
        print("total_samples:", context['total_samples'])
        print("analysis_count:", context['analysis_count'])

        return context


def scan_unified_qr(request):
    """Handle scanning of unified QR codes across all apps"""
    if request.method == 'POST' and request.FILES.get('qr_image'):
        try:
            # Open and decode the uploaded image
            image = Image.open(request.FILES['qr_image'])
            decoded_objects = decode(image)

            if decoded_objects:
                # Parse the unified QR code data
                qr_data = json.loads(decoded_objects[0].data.decode('utf-8'))

                # Verify the QR code structure
                if not all(key in qr_data for key in ['type', 'id']):
                    return JsonResponse({'error': 'Invalid QR code format'}, status=400)

                # Route based on QR type
                if qr_data['type'] == 'patient':
                    return redirect('patients:detail', pk=qr_data['id'])
                elif qr_data['type'] == 'sample':
                    return redirect('samples:detail', pk=qr_data['id'])
                elif qr_data['type'] == 'analysis':
                    return redirect('analysis:detail', pk=qr_data['id'])
                elif qr_data['type'] == 'result':
                    return redirect('results:detail', pk=qr_data['id'])
                elif qr_data['type'] == 'patient_bill':
                    try:
                        bill = Bill.objects.get(id=qr_data['bill_id'])
                        return redirect('billing:bill_detail', pk=bill.id)
                    except Bill.DoesNotExist:
                        return JsonResponse({'error': 'Bill not found'}, status=404)
                else:
                    return JsonResponse({'error': 'Unknown QR code type'}, status=400)

            return JsonResponse({'error': 'No QR code detected'}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid QR code data format'}, status=400)
        except Exception as e:
            logger.error(f"QR scan error: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Error processing QR code'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


def generate_bill_pdf(request, bill_id):
    """Generate PDF version of a bill"""
    try:
        bill = Bill.objects.get(id=bill_id)
        context = {'bill': bill}
        html = render_to_string('billing/bill_pdf.html', context)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="bill_{bill.id}.pdf"'

        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('Error generating PDF', status=500)

        return response
    except Bill.DoesNotExist:
        return HttpResponse('Bill not found', status=404)
    except Exception as e:
        logger.error(f"PDF generation error: {str(e)}")
        return HttpResponse('Error generating PDF', status=500)


def generate_qr_preview(request):
    """Generate a preview of what the unified QR codes will look like"""
    if request.method == 'GET':
        from core.utils import generate_unified_qr
        from django.http import HttpResponse

        # Example data for preview
        qr_types = [
            {'type': 'patient', 'color': 'black'},
            {'type': 'sample', 'color': '#3a7bd5'},
            {'type': 'analysis', 'color': '#6f42c1'},
            {'type': 'result', 'color': '#28a745'},
            {'type': 'patient_bill', 'color': '#007bff'}
        ]

        response = []
        for qr_type in qr_types:
            example_data = {
                'type': qr_type['type'],
                'id': 1,
                'patient_id': 1,
                'timestamp': timezone.now().isoformat()
            }
            if qr_type['type'] == 'patient_bill':
                example_data['bill_id'] = 1

            qr_file = generate_unified_qr(example_data, fill_color=qr_type['color'])
            response.append({
                'type': qr_type['type'],
                'color': qr_type['color'],
                'image': qr_file.read().decode('latin1')  # Simplified for example
            })

        return JsonResponse({'previews': response})

    return JsonResponse({'error': 'Invalid request'}, status=400)


def mark_bill_as_paid(request, bill_id):
    """Mark a bill as paid (AJAX endpoint)"""
    if request.method == 'POST':
        try:
            bill = Bill.objects.get(id=bill_id)
            bill.status = 'paid'
            bill.paid_date = timezone.now()
            bill.save()
            return JsonResponse({'status': 'success'})
        except Bill.DoesNotExist:
            return JsonResponse({'error': 'Bill not found'}, status=404)
        except Exception as e:
            logger.error(f"Error marking bill as paid: {str(e)}")
            return JsonResponse({'error': 'Server error'}, status=500)

    return JsonResponse({'error': 'Invalid method'}, status=405)