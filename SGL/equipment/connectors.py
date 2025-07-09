import json
import requests
import logging
from results.utils import hl7_utils
from analysis.models import Analysis
from .models import LaboratoryEquipment

logger = logging.getLogger(__name__)

class EquipmentConnector:
    def __init__(self, equipment_id):
        self.equipment = LaboratoryEquipment.objects.get(id=equipment_id)

    def send_request(self, analysis_id):
        """Send analysis request to equipment."""
        analysis = Analysis.objects.get(id=analysis_id)
        try:
            if self.equipment.protocol == 'REST':
                response = requests.post(
                    f"http://{self.equipment.ip_address}/api/request",
                    json={'sample_id': analysis.sample.barcode, 'test_code': analysis.analysis_type.code},
                    timeout=5
                )
                return response.json()
            elif self.equipment.protocol == 'HL7':
                # Use your existing HL7 utils
                from results.utils.hl7_utils import create_hl7_message
                hl7_msg = create_hl7_message(analysis)
                # Send via TCP (simplified)
                # ... (implementation depends on equipment)
        except Exception as e:
            logger.error(f"Failed to send to {self.equipment.name}: {str(e)}")
            raise

    def poll_results(self):
        """Poll equipment for pending results (for non-push systems)."""
        try:
            if self.equipment.protocol == 'REST':
                response = requests.get(f"http://{self.equipment.ip_address}/api/results")
                return response.json()
        except Exception as e:
            logger.error(f"Polling failed: {str(e)}")
            return []

    def process_result(self, raw_data):
        """Convert raw equipment data to standard format"""
        try:
            # Standardize different equipment formats
            if self.equipment.model == 'HematologyAnalyzer-X200':
                return self._parse_hematology_data(raw_data)
            elif self.equipment.model == 'ChemistryAnalyzer-C500':
                return self._parse_chemistry_data(raw_data)
        except Exception as e:
            logger.error(f"Data parsing failed: {str(e)}")
            raise