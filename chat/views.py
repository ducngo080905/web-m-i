from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import ChatRoom, Message
from accounts.models import User


@login_required
def chat_room_view(request):
    """User chat với admin"""
    # Tìm hoặc tạo phòng chat
    room, created = ChatRoom.objects.get_or_create(
        user=request.user,
        defaults={'is_active': True}
    )
    
    messages = room.messages.all()[:50]
    
    context = {
        'room': room,
        'messages': messages,
    }
    return render(request, 'chat/chat_room.html', context)


@login_required
def admin_chat_list_view(request):
    """Admin xem danh sách chat"""
    if not request.user.is_admin:
        return redirect('home')
    
    rooms = ChatRoom.objects.filter(is_active=True).order_by('-updated_at')
    return render(request, 'chat/admin_chat_list.html', {'rooms': rooms})


@login_required
def admin_chat_room_view(request, room_id):
    """Admin chat với user"""
    if not request.user.is_admin:
        return redirect('home')
    
    room = get_object_or_404(ChatRoom, id=room_id)
    
    # Mark messages as read
    room.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    messages = room.messages.all()[:100]
    
    context = {
        'room': room,
        'messages': messages,
    }
    return render(request, 'chat/admin_chat_room.html', context)