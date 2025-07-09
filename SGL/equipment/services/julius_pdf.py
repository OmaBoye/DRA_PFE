import os
import requests
from django.conf import settings
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
from reportlab.lib.styles import getSampleStyleSheet
from dotenv import load_dotenv

load_dotenv()


class PDFGeneratorHelpers:
    """Shared helper methods for both generators"""

    @staticmethod
    def _get_unit(parameter):
        units = {
            'WBC': '10³/μL', 'RBC': '10⁶/μL', 'HGB': 'g/dL',
            'HCT': '%', 'PLT': '10³/μL', 'GLU': 'mg/dL',
            'CA': 'mg/dL', 'NA': 'mmol/L', 'K': 'mmol/L',
            'CL': 'mmol/L', 'CO2': 'mmol/L'
        }
        return units.get(parameter, '')

    @staticmethod
    def _get_reference_range(parameter):
        ranges = {
            'WBC': '4.0-11.0', 'RBC': '4.2-6.1', 'HGB': '12.0-18.0',
            'HCT': '37-54', 'PLT': '150-450', 'GLU': '70-100',
            'CA': '8.5-10.2', 'NA': '135-145', 'K': '3.5-5.2',
            'CL': '98-107', 'CO2': '23-29'
        }
        return ranges.get(parameter, 'N/A')

    @staticmethod
    def _is_abnormal(parameter, value):
        try:
            value = float(value)
            ref_range = PDFGeneratorHelpers._get_reference_range(parameter)
            if '-' in ref_range:
                low, high = map(float, ref_range.split('-'))
                return value < low or value > high
        except (ValueError, TypeError):
            return False
        return False


class JuliusPDFGenerator(PDFGeneratorHelpers):
    @staticmethod
    def generate_result_pdf(result):
        """Try Julius AI first, fallback to local if fails"""
        try:
            return JuliusPDFGenerator._generate_with_julius(result)
        except Exception as e:
            print(f"Julius failed ({str(e)}), using local fallback")
            return LocalPDFGenerator.generate_pdf(result)

    @staticmethod
    def _generate_with_julius(result):
        """Julius API implementation"""
        api_key = os.getenv('JULIUS_API_KEY')
        if not api_key:
            raise ValueError("Missing Julius API key")

        response = requests.post(
            f"{os.getenv('JULIUS_BASE_URL', 'https://api.julius.ai/v1')}/generate-pdf",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "template": "medical_lab_report",
                "data": {
                    "patient": {
                        "id": result.sample.barcode,
                        "name": result.sample.patient.full_name,
                        "dob": result.sample.patient.date_of_birth.strftime("%Y-%m-%d"),
                        "gender": result.sample.patient.get_gender_display()
                    },
                    "results": [
                        {
                            "parameter": param,
                            "value": value,
                            "unit": PDFGeneratorHelpers._get_unit(param),
                            "range": PDFGeneratorHelpers._get_reference_range(param),
                            "status": "ABNORMAL" if PDFGeneratorHelpers._is_abnormal(param, value) else "NORMAL"
                        }
                        for param, value in result.values.items()
                    ],
                    "metadata": {
                        "report_date": result.test_date.strftime("%Y-%m-%d %H:%M"),
                        "lab_name": getattr(settings, 'LAB_NAME', 'Clinical Laboratory')
                    }
                }
            },
            timeout=15
        )
        response.raise_for_status()
        return response.content


class LocalPDFGenerator(PDFGeneratorHelpers):
    @staticmethod
    def generate_pdf(result):
        """Fallback PDF generation using ReportLab"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph("Laboratory Results Report", styles['Title']))

        # Patient Info
        patient_info = [
            ["Patient:", result.sample.patient.full_name],
            ["DOB:", result.sample.patient.date_of_birth.strftime("%Y-%m-%d")],
            ["Sample ID:", result.sample.barcode],
            ["Report Date:", result.test_date.strftime("%Y-%m-%d %H:%M")]
        ]
        story.append(Table(patient_info, colWidths=[100, 300]))

        # Results Table
        results_data = [["Test", "Result", "Unit", "Reference Range", "Status"]]
        for param, value in result.values.items():
            is_abnormal = PDFGeneratorHelpers._is_abnormal(param, value)
            results_data.append([
                param,
                str(value),
                PDFGeneratorHelpers._get_unit(param),
                PDFGeneratorHelpers._get_reference_range(param),
                "ABNORMAL" if is_abnormal else "NORMAL"
            ])

        story.append(Table(results_data, colWidths=[100, 80, 60, 100, 80]))
        doc.build(story)
        return buffer.getvalue()