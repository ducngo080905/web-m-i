from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('products/', views.product_list_view, name='product_list'),
    path('product/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('category/<slug:slug>/', views.products_by_category_view, name='products_by_category'),
    path('review/add/<int:product_id>/', views.add_review_view, name='add_review'),
    path('api/search/', views.search_products_api, name='search_products_api'),
]