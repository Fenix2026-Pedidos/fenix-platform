from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Vistas de cliente
    path('', views.order_list, name='order_list'),
    path('create/', views.order_create, name='order_create'),
    path('<int:pk>/', views.order_detail, name='order_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/remove/', views.cart_remove, name='cart_remove'),
    path('cart/update/', views.cart_update, name='cart_update'),
    
    # Vistas de gestión (Manager/Admin)
    path('manage/', views.order_manage_list, name='order_manage_list'),
    path('manage/dashboard/', views.order_dashboard, name='order_dashboard'),
    path('manage/<int:pk>/status/', views.order_update_status, name='order_update_status'),
    path('manage/<int:pk>/eta/', views.order_update_eta, name='order_update_eta'),
    path('manage/<int:pk>/upload-document/', views.order_document_upload, name='order_document_upload'),
    path('manage/<int:pk>/document/<int:doc_id>/delete/', views.order_document_delete, name='order_document_delete'),
]
