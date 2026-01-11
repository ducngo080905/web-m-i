from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list_view, name='notification_list'),
    path('read/<int:notification_id>/', views.mark_as_read_view, name='mark_notification_read'),
    path('read-all/', views.mark_all_read_view, name='mark_all_notifications_read'),
]