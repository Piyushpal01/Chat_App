from django import forms
from django.forms import ModelForm
from .models import *

class ChatmessageCreateForm(ModelForm):
    class Meta:
        model = GroupMessage
        fields = ['body']
        widgets = {
            'body' : forms.TextInput(attrs={
                'placeholder': 'Add Message...',
                'class': 'p-4 text-black',
                'max-length': '300',
                'autofocus': True
            }),
        }