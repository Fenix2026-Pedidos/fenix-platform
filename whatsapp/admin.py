from django.contrib import admin
from .models import WhatsAppLead

@admin.register(WhatsAppLead)
class WhatsAppLeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'sent_successfully', 'page_url')
    list_filter = ('sent_successfully', 'created_at')
    search_fields = ('name', 'message', 'page_url')
    readonly_fields = ('created_at', 'api_response')
    date_hierarchy = 'created_at'
