from django.contrib import admin
from .models import PlatformSettings, AuditLog


@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not PlatformSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    fieldsets = (
        ('Idioma', {'fields': ('default_language',)}),
        ('Email (notificaciones)', {'fields': ('email_from', 'email_from_name')}),
        ('Pedidos', {'fields': ('order_notification_email',)}),
        ('Entrega', {'fields': ('default_delivery_window_hours',)}),
        ('Auditoría', {'fields': ('created_at', 'updated_at')}),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'user', 'action', 'description', 'object_type', 'object_id', 'ip_address']
    list_filter = ['action', 'created_at', 'object_type']
    search_fields = ['user__email', 'description', 'ip_address']
    readonly_fields = ['user', 'action', 'description', 'object_type', 'object_id', 'ip_address', 'user_agent', 'created_at']
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        # No permitir crear logs manualmente
        return False
    
    def has_change_permission(self, request, obj=None):
        # No permitir modificar logs
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Solo super admins pueden borrar logs
        return request.user.is_superuser

