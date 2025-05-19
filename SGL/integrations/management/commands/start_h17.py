from django.core.management.base import BaseCommand
from integrations.mllp_listener import HL7Handler

class Command(BaseCommand):
    help = 'Starts HL7 MLLP listener'

    def handle(self, *args, **options):
        HL7Handler().start()