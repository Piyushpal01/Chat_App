from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from .models import *
from django.http import Http404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import *
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import HttpResponse

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

    # logic to add other user in group chat, nd adding users only if they have verified email
    if chat_group.groupchat_name:
        if request.user not in chat_group.members.all():
            if request.user.emailaddress_set.filter(verified=True).exists():
                chat_group.members.add(request.user)
            else:
                messages.warning(request, "You need to verify email address to join group!")
                return redirect('profile-settings')
            

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
        'chatroom_name':chatroom_name,
        'chat_group': chat_group,
    }

    return render(request, 'a_rtchat/chat.html', context)

# fn to get the private room if not exist then crete it
@login_required
def get_or_create_chatroom(request, username):
    if request.user.username == username:
        return redirect('home')
    
    other_user = get_object_or_404(User, username=username)
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

# create groupchat
@login_required
def create_groupchat(request):
    form = NewGroupchatForm()

    if request.method == "POST":
        form = NewGroupchatForm(request.POST)
        if form.is_valid():
            new_groupchat = form.save(commit=False)
            new_groupchat.admin = request.user
            new_groupchat.save()
            new_groupchat.members.add(request.user)
            return redirect('chatroom', new_groupchat.group_name)
        

    context = {
        'form': form
    }

    return render(request, 'a_rtchat/create_groupchat.html', context)

# edit chatroom - only admin can edit that
@login_required
def chatroom_edit_view(request, chatroom_name):
    # retrieve chat grp object
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)

    if request.user != chat_group.admin:
        raise Http404()
    
    form = ChatroomEditForm(instance=chat_group)
    
    if request.method == 'POST':
        form = ChatroomEditForm(request.POST, instance=chat_group)
        if form.is_valid():
            form.save() # this is for the title

            # removing members, it is the name of the checkbox of inputfield
            remove_members = request.POST.getlist('remove_members') # we got the list of members to remove
            for member_id in remove_members:
                member = User.objects.get(id=member_id)
                # print("MEMBER >>>>> ", member)    # list of members
                chat_group.members.remove(member)
            
            return redirect('chatroom', chatroom_name)

    context = {
        'form': form,
        'chat_group': chat_group,
    }
    return render(request, 'a_rtchat/chatroom_edit.html', context)

@login_required
def chatroom_delete_view(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)

    if request.user != chat_group.admin:
        raise Http404()
    
    if request.method == "POST":
        chat_group.delete()
        messages.success(request, "Chatroom deleted successfully! ")
        return redirect('home')

    return render(request, 'a_rtchat/chatroom_delete.html', {'chat_group':chat_group})

@login_required
def chatroom_leave_view(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)

    if request.user.id not in chat_group.members.values_list("id", flat=True):
        raise Http404()

    if request.method == "POST":
        chat_group.members.remove(request.user)
        messages.success(request, "You left the chatroom.")

        # HTMX request – return JS that closes modal and redirects
        if request.headers.get("HX-Request"):
            return HttpResponse("""
                <script>
                    document.getElementById("leaveModal")?.remove(); // close modal
                    window.location.href = "/"; // redirect
                </script>
            """)

        return redirect('home')

    return render(request, 'a_rtchat/chatroom_leave.html', {'chat_group': chat_group})

# upload files
def chat_file_upload(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)

    # if req is htmx and file request
    if request.htmx and request.FILES:
        file = request.FILES['file']
        message = GroupMessage.objects.create(
            file = file,
            author = request.user,
            group = chat_group,
        )
        channel_layer = get_channel_layer()
        event = {
            'type': 'message_handler',
            'message_id': message.id,
        }

        async_to_sync(channel_layer.group_send)(
            chatroom_name, event
        )
    
    # return empty fn to avoid errors in htmx req
    return HttpResponse()