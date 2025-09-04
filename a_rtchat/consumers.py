from channels.generic.websocket import WebsocketConsumer
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from asgiref.sync import async_to_sync
from .models import *
import json

class ChatroomConsumer(WebsocketConsumer):
    # establish websocket connection
    def connect(self):
        self.user = self.scope['user']
        self.chatroom_name = self.scope['url_route']['kwargs']['chatroom_name']
        self.chatroom = get_object_or_404(ChatGroup, group_name=self.chatroom_name)

        # adding channel layer to group, channel layer is a async operation
        async_to_sync(self.channel_layer.group_add)(
            self.chatroom_name,
            self.channel_name
        )

        # add and update online users
        # first chk if current user is not online yet
        if self.user not in self.chatroom.online_users.all():
            # add user
            self.chatroom.online_users.add(self.user)
            self.update_online_count()  # fn to update online count of group in all browsers

        self.accept()

    # disconnect method, so whenver channel disconnect - leave group
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.chatroom_name, self.channel_name
        )

        # rempve and update online users
        if self.user in self.chatroom.online_users.all():
            # aremove user
            self.chatroom.online_users.remove(self.user)
            self.update_online_count()  # fn to update online count of group in all browsers

    # receive mthd which receive data from form
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        body = text_data_json['body']
        # print(body)

        # store msg in db
        message = GroupMessage.objects.create(
            body = body,
            author = self.user,
            group = self.chatroom
        )

        event = {
            'type':'message_handler',
            'message_id': message.id,
        }

        # broadcasting msg in grp
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name, event
        )
    
    def message_handler(self, event):
        # after saving in DB, call send fn to send data back to frontend
        message_id = event['message_id']    # getting msg object, with the help of msg id
        message = GroupMessage.objects.get(id=message_id)
        context={
            'message':message,
            'user': self.user
        }
        html = render_to_string("a_rtchat/partials/chat_message_p.html", context=context)
        self.send(text_data=html) # send to frontend

    # fn to count users
    def update_online_count(self):
        # count how many users we have in this chatroom
        online_count = self.chatroom.online_users.count() -1    # -1, so that if there is no user, for not confusing, removing that 1 online

        # then we broadcast this number to all members this chatroom 
        event = {
            'type':'online_count_handler',
            'online_count':online_count
        }
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name, event
        )
    
    def online_count_handler(self, event):
        online_count = event['online_count']
        context = {
            'online_count': online_count,
            'chat_group': self.chatroom,
        }
        html = render_to_string("a_rtchat/partials/online_count.html", context)
        self.send(text_data=html)   # send back to client
