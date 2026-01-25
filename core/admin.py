from django.contrib import admin
from .models import PlatformSettings


@admin.register(PlatformSettings)
class PlatformSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not PlatformSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    fieldsets = (
        ('Idioma', {'fields': ('default_language',)}),
        ('Email (notificaciones)', {'fields': ('email_from', 'email_from_name')}),
        ('Entrega', {'fields': ('default_delivery_window_hours',)}),
        ('Auditoría', {'fields': ('created_at', 'updated_at')}),
    )
    readonly_fields = ('created_at', 'updated_at')
