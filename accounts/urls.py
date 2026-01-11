from django.urls import path
from . import views
from . import admin_views

urlpatterns = [
    # User URLs
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password_view, name='reset_password'),
    path('update-location/', views.update_location, name='update_location'),
    path('update-brightness/', views.update_theme_brightness, name='update_brightness'),
    
    # Admin URLs
    path('admin-panel/', admin_views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-panel/users/', admin_views.admin_users_view, name='admin_users'),
    path('admin-panel/users/toggle-lock/<int:user_id>/', admin_views.toggle_user_lock_view, name='toggle_user_lock'),
    path('admin-panel/users/change-role/<int:user_id>/', admin_views.change_user_role_view, name='change_user_role'),
    path('admin-panel/products/', admin_views.admin_products_view, name='admin_products'),
    path('admin-panel/products/add/', admin_views.admin_product_create_view, name='admin_product_create'),
    path('admin-panel/products/edit/<int:product_id>/', admin_views.admin_product_edit_view, name='admin_product_edit'),
    path('admin-panel/products/delete/<int:product_id>/', admin_views.admin_product_delete_view, name='admin_product_delete'),
    path('admin-panel/orders/', admin_views.admin_orders_view, name='admin_orders'),
    path('admin-panel/orders/<int:order_id>/', admin_views.admin_order_detail_view, name='admin_order_detail'),
    path('admin-panel/orders/<int:order_id>/update-status/', admin_views.update_order_status_view, name='update_order_status'),
    path('admin-panel/statistics/', admin_views.admin_statistics_view, name='admin_statistics'),
    path('admin-panel/coupons/', admin_views.admin_coupons_view, name='admin_coupons'),
]