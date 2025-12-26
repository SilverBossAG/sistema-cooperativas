# votaciones/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class VotacionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.id_votacion = self.scope['url_route']['kwargs']['id_votacion']
        self.room_group_name = f'votacion_{self.id_votacion}'

        # Unirse al grupo de esta votación
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Salir del grupo
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Este método recibe el aviso del servidor y se lo pasa al navegador
    async def evento_actualizacion(self, event):
        await self.send(text_data=json.dumps({
            'tipo': 'actualizar',
            'mensaje': 'Nuevos datos disponibles'
        }))