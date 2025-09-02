from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from django.http import Http404
from django.contrib.auth.decorators import login_required
from .forms import *

# Create your views here.
@login_required
def chat_view(request, chatroom_name='public-chat'):
    # retrieve caht grp
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name) 
    
    # retrieve its messages
    chat_messages = chat_group.chat_messages.all()[:30] # fetching only last 30 
    form = ChatmessageCreateForm()

    other_user = None
    if chat_group.is_private:
        if request.user not in chat_group.members.all(): # making sure that login user have permission to access the chat grp, else show 404
            raise Http404()
        # if members is not logged in user, we find other user and break out of loop
        for member in chat_group.members.all():
            if member != request.user:
                other_user = member
                break
            

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

    context = {
        'chat_messages':chat_messages,
        'form':form,
        'other_user':other_user,
        'chatroom_name':chatroom_name
    }

    return render(request, 'a_rtchat/chat.html', context)

# fn to get the private room if not exist then crete it
@login_required
def get_or_create_chatroom(request, username):
    if request.user.username == username:
        return redirect('home')
    
    other_user = User.objects.get(username=username)
    my_chatrooms = request.user.chat_groups.filter(is_private=True)  # checking if chatroom with login user and this other user already exist

    if my_chatrooms.exists():
        for chatroom in my_chatrooms:
            if other_user in chatroom.members.all():
                chatroom = chatroom
                break
            else:
                chatroom = ChatGroup.objects.create(is_private=True)
                chatroom.members.add(other_user, request.user)
    else:
        # create a chatroom
        chatroom = ChatGroup.objects.create(is_private=True)
        chatroom.members.add(other_user, request.user)

    return redirect('chatroom', chatroom.group_name)
