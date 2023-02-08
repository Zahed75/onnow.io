from channels.generic.websocket import AsyncWebsocketConsumer
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync, sync_to_async
import json

from orders.models import OrderTracker

class OrderConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.group_name = 'order_data'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        # print (text_data)
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'send_order',
                'value': text_data,
            }
        )

    async def send_order(self, event):
        print(event['value'])
        await self.send(event['value'])


class OrderStatusTrack(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['order_id']
        self.room_group_name = 'order_%s' % self.room_name
        print(self.room_group_name)

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        order_tracker = OrderTracker.give_order_tracker(self.room_name)
        self.accept()

        self.send(text_data=json.dumps({
            'payload': order_tracker
        }, default=str))

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'order_status_track',
                'payload': text_data
            }
        )

    # Receive message from room group
    def order_status_track(self, event):
        print(event)
        data = json.loads(event['value'])
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'payload': data
        }, default=str))