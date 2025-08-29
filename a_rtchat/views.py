from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from django.contrib.auth.decorators import login_required
from .forms import *

# Create your views here.
@login_required
def chat_view(request):
    # retrieve caht grp
    chat_group = get_object_or_404(ChatGroup, group_name="Private Chat") 
    
    # retrieve its messages
    chat_messages = chat_group.chat_messages.all()[:30] # fetching only last 30 
    form = ChatmessageCreateForm()

    # save in DB
    # if request.method == 'POST':
    if request.htmx: # checking for specifically htmx req
        form = ChatmessageCreateForm(request.POST)
        if form.is_valid():
            # before saving we need to fetch the author and chat grp
            message = form.save(commit=False)
            message.author = request.user
            message.group = chat_group
            message.save()
            context = {
                'message': message,
                'user': request.user
            }
            # send a htmx partial with new msg
            return render(request, 'a_rtchat/partials/chat_message_p.html', context)

    return render(request, 'a_rtchat/chat.html', {'chat_messages':chat_messages, 'form':form})