from django.urls import path
from . import views

app_name = 'recurring'

urlpatterns = [
    path('', views.recurring_order_list, name='recurring_order_list'),
    path('create/', views.recurring_order_create, name='recurring_order_create'),
    path('<int:pk>/', views.recurring_order_detail, name='recurring_order_detail'),
    path('<int:pk>/toggle/', views.recurring_order_toggle, name='recurring_order_toggle'),
    path('<int:pk>/delete/', views.recurring_order_delete, name='recurring_order_delete'),
]
