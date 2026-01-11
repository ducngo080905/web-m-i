from django.urls import path
from . import views

urlpatterns = [
    path('', views.ai_chat_view, name='ai_chat'),
    path('recommend/', views.ai_recommend_view, name='ai_recommend'),
]