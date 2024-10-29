import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from .models import User, Message, Chat


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_type = self.scope['url_route']['kwargs']['chat_type']
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'{self.chat_type}_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        await self.send_system_message(f'{self.scope["user"].username} присоединился к чату.')

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        await self.send_system_message(f'{self.scope["user"].username} покинул чат.')

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        username = text_data_json['username']
        
        user = self.scope["user"]
        chat = await self.get_chat()
        if not chat:
            print("Чат не найден.")
            return

        if username == 'System':
            return

        await self.save_message(chat, user, message)

        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
                'timestamp': timestamp
            }
        )

    async def chat_message(self, event):
        message = event['message']
        username = event.get('username', 'System')
        timestamp = event.get('timestamp')

        await self.send(text_data=json.dumps({
            'username': username,
            'message': message,
            'timestamp': timestamp
        }))

    @database_sync_to_async
    def get_chat(self):
        user = self.scope["user"]
        try:
            if self.chat_type == 'group':
                return Chat.objects.get(id=self.room_name)
            else:
                other_user = User.objects.get(id=self.room_name)
                chat = Chat.get_or_create_private_chat(user, other_user)
                return chat
        except ObjectDoesNotExist:
            print("Chat not found.")
            return None

    @database_sync_to_async
    def save_message(self, chat, user, content):
        # Создаем и сохраняем новое сообщение в базу данных
        return Message.objects.create(
            chat=chat,
            sender=user,
            content=content,
            timestamp=timezone.now()
        )
    
    async def send_system_message(self, message, username='System'):
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Отправляем системное сообщение в группу чата
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,  # Имя пользователя, по умолчанию 'System'
                'timestamp': timestamp
            }
        )
