# hl7_monitor/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

class HL7MonitorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("hl7_updates", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("hl7_updates", self.channel_name)

    async def hl7_message(self, event):
        await self.send(text_data=json.dumps(event))

# hl7_monitor/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/hl7-monitor/$', consumers.HL7MonitorConsumer.as_asgi()),
]