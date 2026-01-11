from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_room_view, name='chat_room'),
    path('admin/', views.admin_chat_list_view, name='admin_chat_list'),
    path('admin/<int:room_id>/', views.admin_chat_room_view, name='admin_chat_room'),
]