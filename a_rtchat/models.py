from django.db import models
from django.contrib.auth.models import User
import shortuuid
import os
from PIL import Image

# Create your models here.
class ChatGroup(models.Model):
    group_name = models.CharField(max_length=130, unique=True, default=shortuuid.uuid)
    groupchat_name = models.CharField(max_length=128, null=True, blank=False)
    admin = models.ForeignKey(User, related_name="groupchats", blank=True, null=True, on_delete=models.SET_NULL)
    # to count users
    online_users = models.ManyToManyField(User, blank=True, related_name="online_users_in_group") 
    members = models.ManyToManyField(User, related_name="chat_groups", blank=True)
    is_private = models.BooleanField(default=False) # field to check if group is private

    def __str__(self):
        return self.group_name

class GroupMessage(models.Model):
    group = models.ForeignKey(ChatGroup, related_name="chat_messages", on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.CharField(max_length=300, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to="files/", blank=True, null=True)

    # to get filename only
    @property
    def filename(self):
        if self.file:
            return os.path.basename(self.file.name)
        else:
            return None

    def __str__(self):
        return self.body if f"{self.author.username}: {self.body}" else f"{self.author.username}: {self.filename}"
    
    class Meta:
        ordering = ['-created'] # to order messages from newest to oldest

    # to chk if file is image or doc
    @property
    def is_image(self):
        try:
            image = Image.open(self.file)
            image.verify()
            return True
        except:
            return False