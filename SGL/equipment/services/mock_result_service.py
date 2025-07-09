import os
import csv
import random
from io import StringIO
from datetime import datetime
from equipment.services.julius_pdf import JuliusPDFGenerator
from dotenv import load_dotenv

load_dotenv()

class MockResultGenerator:
    @staticmethod
    def generate_mock_values(analysis_type):
        """Generate realistic mock values based on test type"""
        ranges = {
            'CBC': {'WBC': (4.0, 11.0), 'RBC': (4.2, 6.1), 'HGB': (12.0, 18.0)},
            'CMP': {'GLU': (70, 110), 'CA': (8.5, 10.2), 'NA': (135, 145)}
        }
        return {param: round(random.uniform(min_val, max_val), 2)
                for param, (min_val, max_val) in ranges.get(analysis_type, {}).items()}

    @staticmethod
    def generate_csv(sample_id, values):
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Parameter', 'Value', 'Units', 'Reference Range'])
        for param, value in values.items():
            writer.writerow([param, value, 'See range', 'Generated mock data'])
        return output.getvalue()

    @staticmethod
    def generate_pdf(sample_id, values):
        return JuliusPDFGenerator.generate_mock_result_pdf({
            'sample_id': sample_id,
            'values': values,
            'timestamp': datetime.now().isoformat()
        })