import requests
from django.conf import settings
from requests.exceptions import RequestException
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def send_diagnostic_report_to_fhir(result):
    """
    Sends a Result instance to a FHIR server as a DiagnosticReport.
    Args:
        result (Result): Django Result model instance
    Returns:
        tuple: (success: bool, response: dict|str)
    """
    fhir_data = result.to_fhir()  # Uses the model's to_fhir() method

    try:
        headers = {
            "Content-Type": "application/fhir+json",
            "Authorization": f"Bearer {settings.FHIR_SERVER_TOKEN}"  # If using auth
        }

        response = requests.post(
            f"{settings.FHIR_SERVER_URL}/DiagnosticReport",
            json=fhir_data,
            headers=headers,
            timeout=10
        )

        if response.status_code in [200, 201]:
            return True, response.json()
        else:
            logger.error(
                f"FHIR API Error: {response.status_code} - {response.text}",
                extra={"result_id": result.id}
            )
            return False, f"FHIR server error: {response.text}"

    except RequestException as e:
        logger.critical(
            f"FHIR Connection Failed: {str(e)}",
            exc_info=True,
            extra={"result_id": result.id}
        )
        return False, f"Connection error: {str(e)}"


def create_fhir_observation(result, test_name, test_value):
    """
    Creates individual FHIR Observation for each test result.
    Args:
        result (Result): Parent Result instance
        test_name (str): Name of the test (e.g., "glucose")
        test_value (str): Test result value (e.g., "95 mg/dL")
    Returns:
        dict: FHIR Observation resource
    """
    return {
        "resourceType": "Observation",
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "laboratory"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": _get_loinc_code(test_name),  # Implement your mapping
                "display": test_name
            }]
        },
        "subject": {
            "reference": f"Patient/{result.patient.id}"
        },
        "effectiveDateTime": datetime.now().isoformat(),
        "issued": datetime.now().isoformat(),
        "valueString": str(test_value),
        "specimen": {
            "reference": f"Specimen/{result.sample.id}"
        }
    }


def _get_loinc_code(test_name):
    """
    Maps local test names to LOINC codes.
    Replace with your lab's actual mappings.
    """
    loinc_map = {
        "glucose": "2345-7",
        "hemoglobin": "718-7",
        # Add your lab's test mappings here
    }
    return loinc_map.get(test_name.lower(), "LP29693-6")  # Default unknown code