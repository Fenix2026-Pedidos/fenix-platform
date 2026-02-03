from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    # Vistas públicas
    path('', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    
    # Vistas de gestión (Manager/Admin)
    path('manage/', views.product_manage_list, name='product_manage_list'),
    path('manage/create/', views.product_create, name='product_create'),
    path('manage/<int:pk>/', views.product_manage_detail, name='product_manage_detail'),
    path('manage/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('manage/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('manage/<int:pk>/stock/', views.product_stock_update, name='product_stock_update'),
]
