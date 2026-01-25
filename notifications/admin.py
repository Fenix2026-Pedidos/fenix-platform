from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'event_type', 'is_read', 'created_at')
    list_filter = ('event_type', 'is_read')
    search_fields = ('user__email', 'subject_es', 'subject_zh_hans')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {'fields': ('user', 'event_type', 'is_read')}),
        ('Contenido ES', {'fields': ('subject_es', 'message_es')}),
        ('Contenido ZH', {'fields': ('subject_zh_hans', 'message_zh_hans')}),
        ('Auditoría', {'fields': ('created_at',)}),
    )
