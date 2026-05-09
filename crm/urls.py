from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    path('leads/', views.leads_list, name='leads_list'),
    path('leads/<uuid:lead_uuid>/', views.lead_detail, name='lead_detail'),
    path('leads/<uuid:lead_uuid>/update/', views.update_lead, name='update_lead'),
    path('leads/<uuid:lead_uuid>/add-message/', views.add_lead_message, name='add_lead_message'),
]
