# integrations/mllp_listener.py
import socket
import logging
import time
from django.conf import settings
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from hl7_monitor.models import HL7Message
from patients.models import Patient
from samples.models import Sample, SampleType
from results.models import Result

logger = logging.getLogger(__name__)


class MLLPServer:
    """Minimal MLLP server implementation with WebSocket support"""
    START_BYTE = b'\x0b'  # VT character
    END_BYTE = b'\x1c\r'  # FS + CR

    def __init__(self, host='0.0.0.0', port=2575):
        self.host = host
        self.port = port
        self.channel_layer = get_channel_layer()

    def _broadcast_update(self, message_data):
        """Send real-time update via WebSocket"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                "hl7_updates",
                {
                    "type": "hl7.message",
                    "message": message_data
                }
            )
        except Exception as e:
            logger.error(f"WebSocket broadcast failed: {str(e)}")

    def handle_message(self, raw_message):
        """Override in subclass"""
        raise NotImplementedError

    def start(self):
        """Start listening for MLLP messages"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen()
            logger.info(f"MLLP server listening on {self.host}:{self.port}")

            while True:
                conn, addr = s.accept()
                with conn:
                    try:
                        data = conn.recv(4096)
                        if not data:
                            continue

                        # Validate MLLP envelope
                        if data.startswith(self.START_BYTE) and data.endswith(self.END_BYTE):
                            raw_message = data[1:-2].decode('utf-8')  # Strip wrappers
                            response = self.handle_message(raw_message)
                            conn.sendall(self.START_BYTE + response.encode() + self.END_BYTE)
                        else:
                            logger.warning(f"Invalid MLLP message from {addr}")
                            conn.sendall(
                                self.START_BYTE +
                                self.create_ack('ERROR', ack_code='AE').encode() +
                                self.END_BYTE
                            )

                    except Exception as e:
                        logger.error(f"Connection error from {addr}: {str(e)}")
                        if 'conn' in locals():
                            conn.sendall(
                                self.START_BYTE +
                                self.create_ack('ERROR', ack_code='AE').encode() +
                                self.END_BYTE
                            )


class HL7Handler(MLLPServer):
    """Handles HL7 message processing with WebSocket notifications"""

    def handle_message(self, raw_message):
        """Route HL7 messages to appropriate processors"""
        start_time = time.time()
        segments = [s.split('|') for s in raw_message.split('\r') if s]
        msh = segments[0]
        message_type = msh[8] if len(msh) > 8 else None
        control_id = msh[9] if len(msh) > 9 else 'UNKNOWN'

        # Create log entry
        hl7_msg = HL7Message.objects.create(
            message_type=message_type,
            raw_message=raw_message,
            direction='IN',
            status='RECEIVED',
            control_id=control_id
        )
        self._broadcast_update({
            'id': hl7_msg.id,
            'type': message_type,
            'status': 'RECEIVED',
            'timestamp': hl7_msg.timestamp.isoformat(),
            'control_id': control_id
        })

        try:
            # Message type routing
            if message_type == 'ADT^A01':
                result = self.process_admission(segments, control_id)
            elif message_type == 'ORM^O01':
                result = self.process_order(segments, control_id)
            elif message_type == 'ORU^R01':
                result = self.process_result(segments, control_id)
            else:
                logger.warning(f"Unsupported message type: {message_type}")
                result = self.create_ack(control_id, ack_code='AE')

            hl7_msg.status = 'PROCESSED'
            return result

        except Exception as e:
            logger.error(f"Message processing failed: {str(e)}", exc_info=True)
            hl7_msg.status = 'ERROR'
            hl7_msg.error_message = str(e)[:200]  # Truncate long errors
            return self.create_ack(control_id, ack_code='AE')

        finally:
            # Update processing metrics
            hl7_msg.processing_time = time.time() - start_time
            hl7_msg.save()
            self._broadcast_update({
                'id': hl7_msg.id,
                'type': message_type,
                'status': hl7_msg.status,
                'timestamp': hl7_msg.timestamp.isoformat(),
                'processing_time': hl7_msg.processing_time,
                'control_id': control_id
            })

    @transaction.atomic
    def process_admission(self, segments, control_id):
        """Process ADT^A01 (Patient Admission)"""
        pid = next(s for s in segments if s[0] == 'PID')

        patient, created = Patient.objects.update_or_create(
            external_id=pid[3][0][1],  # PID.3.2
            defaults={
                'first_name': pid[5][0][1],  # PID.5.2
                'last_name': pid[5][0][0],  # PID.5.1
                'date_of_birth': pid[7][0],  # PID.7
                'gender': pid[8][0] if len(pid) > 8 else 'U'
            }
        )

        logger.info(f"{'Created' if created else 'Updated'} patient {patient.external_id}")
        return self.create_ack(control_id)

    @transaction.atomic
    def process_order(self, segments, control_id):
        """Process ORM^O01 (Lab Order)"""
        orc = next(s for s in segments if s[0] == 'ORC')
        obr = next(s for s in segments if s[0] == 'OBR')

        sample = Sample.objects.create(
            patient=Patient.objects.get(external_id=orc[2]),  # ORC.2
            analysis_type=SampleType.objects.get(loinc_code=obr[4][0][0]),  # OBR.4
            status='received',
            barcode=f"LAB-{obr[4][0][0]}-{orc[2]}",
            collection_date=obr[7][0] if len(obr) > 7 else None,  # OBR.7
            ordering_provider=orc[12][0] if len(orc) > 12 else None  # ORC.12
        )

        logger.info(f"Created sample {sample.barcode}")
        return self.create_ack(control_id)

    @transaction.atomic
    def process_result(self, segments, control_id):
        """Process ORU^R01 (Lab Result)"""
        pid = next(s for s in segments if s[0] == 'PID')
        obr = next(s for s in segments if s[0] == 'OBR')
        obx_list = [s for s in segments if s[0] == 'OBX']

        # Get/create local records
        sample = Sample.objects.get(barcode=obr[4][0][0])  # OBR.4

        # Create result with all OBX values
        result = Result.objects.create(
            sample=sample,
            values={
                obx[3][0][0]: {  # OBX.3 (LOINC code)
                    'value': obx[5][0],  # OBX.5
                    'unit': obx[6][0] if len(obx) > 6 else None,  # OBX.6
                    'abnormal_flag': obx[8][0] if len(obx) > 8 else None  # OBX.8
                } for obx in obx_list
            },
            status='completed',
            test_date=obr[7][0] if len(obr) > 7 else None,  # OBR.7
            performer=obr[34][0] if len(obr) > 34 else None  # OBR.34
        )

        logger.info(f"Created result for sample {sample.barcode} with {len(obx_list)} OBX segments")
        return self.create_ack(control_id)

    def create_ack(self, control_id, ack_code='AA'):
        """Generate HL7 ACK message with current timestamp"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return (
            f"MSH|^~\&|LIS|LAB|||{timestamp}||ACK|{control_id}|P|2.5\r"
            f"MSA|{ack_code}|{control_id}"
        )


def start_server():
    """Start the MLLP server with enhanced logging"""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--daemon', action='store_true', help='Run in background')
    args = parser.parse_args()

    if args.daemon:
        import daemon
        with daemon.DaemonContext():
            HL7Handler().start()
    else:
        HL7Handler().start()