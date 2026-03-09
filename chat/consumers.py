import json
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Message, Profile

MAX_MESSAGE_LENGTH = 2000


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.me = self.scope['user']

        if not self.me.is_authenticated:
            await self.close()
            return

        self.other_username = self.scope['url_route']['kwargs']['username']

        if self.me.username == self.other_username:
            await self.close()
            return

        other_exists = await self.user_exists(self.other_username)
        if not other_exists:
            await self.close()
            return

        names = sorted([self.me.username, self.other_username])
        self.room_group_name = f"chat_{names[0]}--{names[1]}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Send other user's current status to me when I open chat
        other_status = await self.get_other_status(self.other_username)
        await self.send(text_data=json.dumps({
            'type':      'status',
            'user':      self.other_username,
            'is_online': other_status['is_online'],
            'last_seen': other_status['last_seen'],
        }))

        # Mark unread messages as read & notify the other side
        await self.mark_messages_read(self.me.username, self.other_username)
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'messages_read', 'reader': self.me.username}
        )

    async def disconnect(self, close_code):
        if not hasattr(self, 'room_group_name'):
            return
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, ValueError):
            return

        if not isinstance(data, dict):
            return

        message = data.get('message', '')

        if not isinstance(message, str):
            return
        message = message.strip()
        if not message:
            return
        if len(message) > MAX_MESSAGE_LENGTH:
            await self.send(text_data=json.dumps({
                'type':  'error',
                'error': f'Message too long (max {MAX_MESSAGE_LENGTH} characters).',
            }))
            return

        msg_id, timestamp = await self.save_message(
            self.me.username, self.other_username, message
        )
        if msg_id is None:
            await self.send(text_data=json.dumps({
                'type':  'error',
                'error': 'Message could not be saved.',
            }))
            return

        await self.channel_layer.group_send(    
            self.room_group_name,
            {
                'type':      'chat_message',
                'message':   message,
                'sender':    self.me.username,
                'timestamp': timestamp,
                'msg_id':    msg_id,
            }
        )
        await self.channel_layer.group_send(
            'online_users',
            {
                'type':     'new_message_notify',
                'sender':   self.me.username,
                'receiver': self.other_username,
            }
        )
        
        
        
        

        # If receiver is online, mark as read immediately → instant ✓✓
        receiver_online = await self.is_user_online(self.other_username)
        if receiver_online:
            await self.mark_messages_read(self.me.username, self.other_username)
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'messages_read', 'reader': self.other_username}
            )

    # Group event handlers ─

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type':      'message',
            'message':   event['message'],
            'sender':    event['sender'],
            'timestamp': event['timestamp'],
            'msg_id':    event['msg_id'],
        }))

    async def status_update(self, event):
        await self.send(text_data=json.dumps({
            'type':      'status',
            'user':      event['user'],
            'is_online': event['is_online'],
            'last_seen': event['last_seen'],
        }))
        

    async def messages_read(self, event):
        await self.send(text_data=json.dumps({
            'type':   'read',
            'reader': event['reader'],
        }))

    # ─ DB helpers ──

    @database_sync_to_async
    def user_exists(self, username):
        return User.objects.filter(username=username).exists()

    @database_sync_to_async
    def is_user_online(self, username):
        try:
            profile = Profile.objects.get(user__username=username)
            return profile.is_online
        except Profile.DoesNotExist:
            return False

    @database_sync_to_async
    def mark_messages_read(self, reader_username, sender_username):
        try:
            sender = User.objects.get(username=sender_username)
            reader = User.objects.get(username=reader_username)
        except User.DoesNotExist:
            return
        Message.objects.filter(
            sender=sender, receiver=reader, is_read=False
        ).update(is_read=True)

    @database_sync_to_async
    def get_other_status(self, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return {'is_online': False, 'last_seen': '⚫ Offline'}
        profile, _ = Profile.objects.get_or_create(user=user)

        if profile.is_online:
            return {'is_online': True, 'last_seen': ''}
        if profile.last_seen:
            local_time = timezone.localtime(profile.last_seen)
            return {
                'is_online': False,
                'last_seen': local_time.strftime('Last seen %d %b at %I:%M %p'),
            }
        return {'is_online': False, 'last_seen': '⚫ Offline'}

    @database_sync_to_async
    def save_message(self, sender_username, receiver_username, content):
        try:
            sender   = User.objects.get(username=sender_username)
            receiver = User.objects.get(username=receiver_username)
        except User.DoesNotExist:
            return None, None

        msg = Message.objects.create(
            sender=sender, receiver=receiver, content=content
        )
        local_time = timezone.localtime(msg.timestamp)
        return msg.id, local_time.strftime('%I:%M %p')

    @database_sync_to_async
    def update_status(self, username, is_online):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return ''
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.is_online = is_online

        if not is_online:
            profile.last_seen = timezone.now()
            profile.save(update_fields=['is_online', 'last_seen'])
            local_time = timezone.localtime(profile.last_seen)
            return local_time.strftime('Last seen %d %b at %I:%M %p')

        profile.save(update_fields=['is_online'])
        return ''


class OnlineConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add('online_users', self.channel_name)
        await self.accept()

  
        await self.update_status(self.user.username, True)

        await self.channel_layer.group_send(
            'online_users',
            {
                'type':      'status_update',
                'user':      self.user.username,
                'is_online': True,
            }
        )

    async def disconnect(self, close_code):
        if not hasattr(self, 'user'):
            return

      
        last_seen = await self.update_status(self.user.username, False)

      
        await self.channel_layer.group_send(
            'online_users',
            {
                'type':      'status_update',
                'user':      self.user.username,
                'is_online': False,
                'last_seen': last_seen,
            }
        )

        await self.channel_layer.group_discard('online_users', self.channel_name)

    async def status_update(self, event):
        await self.send(text_data=json.dumps({
            'type':      'status',
            'user':      event['user'],
            'is_online': event['is_online'],
            'last_seen': event.get('last_seen', ''),
        }))
    async def new_message_notify(self, event):
        await self.send(text_data=json.dumps({
            'type':     'new_message',
            'sender':   event['sender'],
            'receiver': event['receiver'],
        }))
        

    @database_sync_to_async
    def update_status(self, username, is_online):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return ''
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.is_online = is_online

        if not is_online:
            profile.last_seen = timezone.now()
            profile.save(update_fields=['is_online', 'last_seen'])
            local_time = timezone.localtime(profile.last_seen)
            return local_time.strftime('Last seen %d %b at %I:%M %p')

        profile.save(update_fields=['is_online'])
        return ''