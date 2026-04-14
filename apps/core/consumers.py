import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class RobotAlertsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        
        # Verificar si el usuario está autenticado, sino rechazar
        if user.is_anonymous:
            await self.close()
            return
            
        # Nos unimos a un grupo específico para las alertas del usuario
        self.group_name = f"user_alerts_{user.id}"
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        pass # Por ahora no procesamos mensajes entrantes del frontend

    async def send_alert(self, event):
        """
        Manejador para el evento 'send_alert'.
        """
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'alert',
            'data': message
        }))
