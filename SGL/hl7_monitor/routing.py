# hl7_monitor/routing.py
from django.urls import re_path
from .consumers import HL7MonitorConsumer

websocket_urlpatterns = [
    re_path(r'ws/hl7-monitor/$', HL7MonitorConsumer.as_asgi()),
]