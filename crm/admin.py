from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import CRMLead, CRMLeadMessage

class CRMLeadMessageInline(admin.TabularInline):
    model = CRMLeadMessage
    extra = 0
    readonly_fields = ('channel', 'sender', 'message', 'timestamp', 'metadata')
    can_delete = False

@admin.register(CRMLead)
class CRMLeadAdmin(admin.ModelAdmin):
    list_display = (
        'get_serial_id_display',
        'full_name',
        'company_name',
        'phone',
        'channel',
        'lead_status',
        'validation_status',
        'priority',
        'geographic_zone',
        'created_at',
    )
    list_filter = (
        'channel',
        'lead_status',
        'validation_status',
        'priority',
        'geographic_zone',
        'created_at',
    )
    search_fields = (
        'full_name',
        'company_name',
        'phone',
        'email',
        'notes',
    )
    readonly_fields = ('id', 'uuid', 'created_at', 'updated_at', 'last_contact_at')
    inlines = [CRMLeadMessageInline]
    
    fieldsets = (
        (_('Identificación'), {
            'fields': ('id', 'uuid', 'full_name', 'company_name', 'geographic_zone')
        }),
        (_('Contacto'), {
            'fields': ('phone', 'email')
        }),
        (_('Canal y Origen'), {
            'fields': ('channel', 'source', 'first_message')
        }),
        (_('Estado Comercial y de Control'), {
            'fields': ('lead_status', 'validation_status', 'priority', 'assigned_to', 'estimated_value')
        }),
        (_('Notas'), {
            'fields': ('notes',)
        }),
        (_('Tiempos'), {
            'fields': ('last_contact_at', 'created_at', 'updated_at')
        }),
    )

    def get_serial_id_display(self, obj):
        return obj.serial_id
    get_serial_id_display.short_description = _("ID Consecutivo")


@admin.register(CRMLeadMessage)
class CRMLeadMessageAdmin(admin.ModelAdmin):
    list_display = ('lead', 'channel', 'sender', 'message_snippet', 'timestamp')
    list_filter = ('channel', 'sender', 'timestamp')
    search_fields = ('message', 'lead__full_name')
    readonly_fields = ('lead', 'channel', 'sender', 'message', 'timestamp', 'metadata')

    def message_snippet(self, obj):
        if len(obj.message) > 75:
            return f"{obj.message[:72]}..."
        return obj.message
    message_snippet.short_description = _("Mensaje")
