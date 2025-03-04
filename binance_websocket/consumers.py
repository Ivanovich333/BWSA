import json
from channels.generic.websocket import AsyncWebsocketConsumer

class BinanceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        
        await self.channel_layer.group_add(
            "binance_data",
            self.channel_name
        )
        
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'You are now connected to the Binance WebSocket server!'
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "binance_data",
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.dumps({
            'type': 'echo',
            'message': 'Received: ' + text_data,
        })
        
        await self.send(text_data=text_data_json)
    
    async def binance_message(self, event):
        await self.send(text_data=json.dumps(event)) 