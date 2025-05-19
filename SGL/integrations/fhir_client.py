import requests
import json
from django.conf import settings


class FHIRClient:
    def __init__(self):
        self.base_url = getattr(settings, 'FHIR_SERVER_URL', 'https://hapi.fhir.org/baseR4')

    def send_observation(self, result):
        """Convert Django Result to FHIR Observation"""
        observation = {
            "resourceType": "Observation",
            "status": "final",
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "TODO_LOINC_CODE",
                    "display": str(result.analysis_type)
                }]
            },
            "subject": {
                "reference": f"Patient/{result.sample.patient.external_id}"
            },
            "valueQuantity": {
                "value": result.values.get('value'),
                "unit": result.values.get('unit'),
                "system": "http://unitsofmeasure.org"
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/Observation",
                headers={'Content-Type': 'application/fhir+json'},
                data=json.dumps(observation)
            )
            return response.json()
        except Exception as e:
            print(f"FHIR error: {str(e)}")
            return None

    def search(self, resource_type, **params):
        """Search FHIR resources with flexible parameters"""
        query = '&'.join(f"{k}={v}" for k,v in params.items())
        response = requests.get(
            f"{self.base_url}/{resource_type}?{query}",
            headers={'Accept': 'application/fhir+json'}
        )
        return self._parse_bundle(response.json())

    def _parse_bundle(self, bundle):
        """Extract entries from FHIR Bundle"""
        return {
            'total': bundle.get('total', 0),
            'entries': [
                self._map_resource(entry['resource'])
                for entry in bundle.get('entry', [])
            ]
        }

    def _map_resource(self, resource):
        """Convert FHIR resource to simplified format"""
        if resource['resourceType'] == 'Patient':
            return {
                'id': resource['id'],
                'name': resource['name'][0]['given'][0] + ' ' + resource['name'][0]['family'],
                'birth_date': resource.get('birthDate')
            }
        elif resource['resourceType'] == 'Observation':
            return {
                'code': resource['code']['coding'][0]['display'],
                'value': resource.get('valueQuantity', {}).get('value')
            }
        return resource