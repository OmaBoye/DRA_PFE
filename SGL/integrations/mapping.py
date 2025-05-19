# integrations/mapping.py
from fhir.resources.patient import Patient as FHIRPatient
from fhir.resources.observation import Observation as FHIRObservation
from fhir.resources.humanname import HumanName
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.quantity import Quantity
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class HL7FHIRMapper:
    """Converts HL7 v2.x messages to FHIR Resources"""

    @staticmethod
    def pid_to_fhir(pid_segment):
        """
        Convert HL7 PID segment to FHIR Patient
        PID|1||PAT123^^^HOSPITAL^MR||DOE^JOHN^A||19700101|M
        """
        try:
            patient = FHIRPatient.construct()

            # Add identifier (PID.3)
            if len(pid_segment) > 3 and pid_segment[3]:
                patient.identifier = [{
                    "system": f"urn:oid:{settings.HL7_OID}",
                    "value": pid_segment[3][0][1]  # PAT123
                }]

            # Add name (PID.5)
            if len(pid_segment) > 5 and pid_segment[5]:
                name = HumanName.construct()
                name.family = pid_segment[5][0][0]  # DOE
                name.given = [pid_segment[5][0][1]]  # JOHN
                patient.name = [name]

            # Add birthDate (PID.7)
            if len(pid_segment) > 7 and pid_segment[7]:
                patient.birthDate = pid_segment[7][0]  # 19700101

            # Add gender (PID.8)
            if len(pid_segment) > 8 and pid_segment[8]:
                patient.gender = pid_segment[8][0].lower()  # m → male

            return patient

        except Exception as e:
            logger.error(f"PID→FHIR mapping failed: {str(e)}")
            raise

    @staticmethod
    def obx_to_fhir(obx_segments, patient_ref):
        """
        Convert HL7 OBX segments to FHIR Observations
        OBX||NM|6690-2^WBC||7.5|10^3/uL||||F
        """
        observations = []

        for obx in obx_segments:
            try:
                obs = FHIRObservation.construct()
                obs.status = "final"

                # Code (OBX.3)
                coding = Coding.construct()
                coding.system = "http://loinc.org"
                coding.code = obx[3][0][0]  # 6690-2
                coding.display = obx[3][0][1] if len(obx[3][0]) > 1 else None  # WBC

                obs.code = CodeableConcept.construct()
                obs.code.coding = [coding]

                # Value (OBX.5) and Unit (OBX.6)
                if len(obx) > 5 and obx[5]:
                    obs.valueQuantity = Quantity.construct()
                    obs.valueQuantity.value = float(obx[5][0])

                    if len(obx) > 6 and obx[6]:
                        obs.valueQuantity.unit = obx[6][0]
                        obs.valueQuantity.system = "http://unitsofmeasure.org"

                # Patient Reference
                obs.subject = {"reference": patient_ref}

                observations.append(obs)

            except Exception as e:
                logger.error(f"OBX→FHIR mapping failed for segment {obx}: {str(e)}")
                continue

        return observations