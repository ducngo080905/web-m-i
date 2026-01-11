from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('success/<int:order_id>/', views.order_success_view, name='order_success'),
    path('history/', views.order_history_view, name='order_history'),
    path('detail/<int:order_id>/', views.order_detail_view, name='order_detail'),
    path('cancel/<int:order_id>/', views.cancel_order_view, name='cancel_order'),
    path('buy-now/<int:product_id>/', views.buy_now_view, name='buy_now'),
    path('buy-now/checkout/', views.buy_now_checkout_view, name='buy_now_checkout'),
]