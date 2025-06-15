# integrations/mllp_listener.py
import socket
import logging
import time
import json
from django.conf import settings
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import ssl
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from cryptography import x509
import datetime

logger = logging.getLogger(__name__)


class MLLPServer:
    """Secure MLLP server implementation with WebSocket notifications"""
def __init__(self, host='0.0.0.0', port=2576):
    START_BYTE = b'\x0b'  # VT character
    END_BYTE = b'\x1c\r'  # FS + CR

    def __init__(self, host='0.0.0.0', port=2575):
        self.host = host
        self.port = port
        self.channel_layer = get_channel_layer()
        self.ssl_context = self._create_ssl_context()

    def _create_ssl_context(self):
        """Generate self-signed cert and key if they don't exist"""
        try:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain('cert.pem', 'key.pem')
            return context
        except FileNotFoundError:
            logger.warning("Certificate files not found. Generating new ones...")
            self._generate_self_signed_cert()
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain('cert.pem', 'key.pem')
            return context

    def _generate_self_signed_cert(self):
        """Generate self-signed certificate and private key"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
        )

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
        ).sign(private_key, hashes.SHA256())

        # Save private key
        with open("key.pem", "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ))

        # Save certificate
        with open("cert.pem", "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        logger.info("Generated new cert.pem and key.pem")

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

    def _validate_hl7(self, raw_message):
        """Basic HL7 message validation"""
        if not raw_message.startswith("MSH|"):
            logger.error("Invalid HL7: Missing MSH segment")
            return False
        segments = raw_message.split('\r')
        if len(segments) < 2:
            logger.error("Invalid HL7: No segments found")
            return False
        return True

    def start(self):
        """Start secure MLLP server"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host, self.port))
            sock.listen(5)

            with self.ssl_context.wrap_socket(sock, server_side=True) as ssock:
                logger.info(f"Secure MLLP server listening on {self.host}:{self.port}")

                while True:
                    try:
                        conn, addr = ssock.accept()
                        with conn:
                            client_ip = addr[0]
                            logger.info(f"Connection from {client_ip}")

                            data = conn.recv(4096)
                            if not data:
                                continue

                            # Validate MLLP envelope
                            if data.startswith(self.START_BYTE) and data.endswith(self.END_BYTE):
                                raw_message = data[1:-2].decode('utf-8')  # Strip wrappers

                                if self._validate_hl7(raw_message):
                                    handler = HL7Handler()
                                    response = handler.handle_message(raw_message)
                                    conn.sendall(self.START_BYTE + response.encode() + self.END_BYTE)
                                else:
                                    logger.warning(f"Invalid HL7 message from {client_ip}")
                                    conn.sendall(
                                        self.START_BYTE +
                                        self.create_ack('ERROR', ack_code='AE').encode() +
                                        self.END_BYTE
                                    )
                            else:
                                logger.warning(f"Invalid MLLP envelope from {client_ip}")
                                conn.sendall(
                                    self.START_BYTE +
                                    self.create_ack('ERROR', ack_code='AE').encode() +
                                    self.END_BYTE
                                )

                    except Exception as e:
                        logger.error(f"Connection error: {str(e)}")
                        if 'conn' in locals():
                            try:
                                conn.sendall(
                                    self.START_BYTE +
                                    self.create_ack('ERROR', ack_code='AE').encode() +
                                    self.END_BYTE
                                )
                            except:
                                pass

    def create_ack(self, control_id, ack_code='AA'):
        """Generate HL7 ACK message"""
        timestamp = time.strftime('%Y%m%d%H%M%S')
        return (
            f"MSH|^~\&|LIS|LAB|||{timestamp}||ACK|{control_id}|P|2.5\r"
            f"MSA|{ack_code}|{control_id}"
        )


class HL7Handler:
    """Process HL7 messages and store in database"""

    def __init__(self):
        self.message_processors = {
            'ADT^A01': self.process_admission,
            'ORM^O01': self.process_order,
            'ORU^R01': self.process_result
        }

    def handle_message(self, raw_message):
        start_time = time.time()
        segments = [s.split('|') for s in raw_message.split('\r') if s]
        msh = segments[0]
        message_type = msh[8] if len(msh) > 8 else None
        control_id = msh[9] if len(msh) > 9 else 'UNKNOWN'

        # Create log entry
        from hl7_monitor.models import HL7Message
        hl7_msg = HL7Message.objects.create(
            message_type=message_type,
            raw_message=raw_message,
            direction='IN',
            status='RECEIVED',
            control_id=control_id
        )

        # Broadcast initial receipt
        self._broadcast_update({
            'id': hl7_msg.id,
            'type': message_type,
            'status': 'RECEIVED',
            'timestamp': hl7_msg.timestamp.isoformat(),
            'control_id': control_id
        })

        try:
            # Route message to processor
            processor = self.message_processors.get(message_type)
            if processor:
                result = processor(segments, control_id)
                hl7_msg.status = 'PROCESSED'
            else:
                logger.warning(f"Unsupported message type: {message_type}")
                result = self.create_ack(control_id, ack_code='AE')
                hl7_msg.status = 'UNSUPPORTED'

            return result

        except Exception as e:
            logger.error(f"Message processing failed: {str(e)}", exc_info=True)
            hl7_msg.status = 'ERROR'
            hl7_msg.error_message = str(e)[:200]
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

    def _broadcast_update(self, message_data):
        """Send update via WebSocket"""
        channel_layer = get_channel_layer()
        try:
            async_to_sync(channel_layer.group_send)(
                "hl7_updates",
                {
                    "type": "hl7.message",
                    "message": message_data
                }
            )
        except Exception as e:
            logger.error(f"WebSocket broadcast failed: {str(e)}")

    @transaction.atomic
    def process_admission(self, segments, control_id):
        """Process ADT^A01 (Patient Admission)"""
        pid = next(s for s in segments if s[0] == 'PID')
        from patients.models import Patient

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
        from patients.models import Patient
        from samples.models import Sample, SampleType

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
        from samples.models import Sample
        from results.models import Result

        # Get sample and create result
        sample = Sample.objects.get(barcode=obr[4][0][0])  # OBR.4
        result_values = {
            obx[3][0][0]: {  # OBX.3 (LOINC code)
                'value': obx[5][0],  # OBX.5
                'unit': obx[6][0] if len(obx) > 6 else None,  # OBX.6
                'abnormal_flag': obx[8][0] if len(obx) > 8 else None  # OBX.8
            } for obx in obx_list
        }

        result = Result.objects.create(
            sample=sample,
            values=result_values,
            status='completed',
            test_date=obr[7][0] if len(obr) > 7 else None,  # OBR.7
            performer=obr[34][0] if len(obr) > 34 else None  # OBR.34
        )

        logger.info(f"Created result for sample {sample.barcode} with {len(obx_list)} OBX segments")
        return self.create_ack(control_id)

    def create_ack(self, control_id, ack_code='AA'):
        """Generate HL7 ACK message"""
        timestamp = time.strftime('%Y%m%d%H%M%S')
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

    server = MLLPServer()
    logger.info("Starting HL7 MLLP server...")
    server.start()