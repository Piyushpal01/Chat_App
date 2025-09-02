from django.db import models
from django.contrib.auth.models import User
import shortuuid

# Create your models here.
class ChatGroup(models.Model):
    group_name = models.CharField(max_length=130, unique=True, default=shortuuid.uuid)
    # to count users
    online_users = models.ManyToManyField(User, blank=True, related_name="online_users_in_group") 
    members = models.ManyToManyField(User, related_name="chat_groups", blank=True)
    is_private = models.BooleanField(default=False) # field to check if group is private

    def __str__(self):
        return self.group_name

class GroupMessage(models.Model):
    group = models.ForeignKey(ChatGroup, related_name="chat_messages", on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.CharField(max_length=300)
    created = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f'{self.author.username} : {self.body}'
    
    class Meta:
        ordering = ['-created'] # to order messages from newest to oldest