from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import (
    User, EmailVerificationToken, UserPreferences, SecuritySettings,
    UserSession, LoginHistory, ProfileAuditLog
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'display_name', 'company', 'role', 'status', 'profile_completed_badge', 'language', 'is_active', 'date_joined')
    list_filter = ('role', 'status', 'language', 'is_active', 'is_staff', 'email_verified', 'profile_completed')
    search_fields = ('email', 'full_name', 'first_name', 'last_name', 'company', 'phone', 'ciudad', 'provincia')
    ordering = ('-date_joined',)
    filter_horizontal = ()
    readonly_fields = ('uuid', 'last_login', 'last_login_at', 'last_login_ip', 'date_joined', 'updated_at', 'profile_completed')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Identificación', {'fields': ('uuid',)}),
        ('Datos Personales', {
            'fields': ('first_name', 'last_name', 'full_name', 'phone', 'avatar')
        }),
        ('Empresa', {'fields': ('company',)}),
        ('Contacto Operativo', {
            'fields': ('telefono_empresa', 'telefono_reparto'),
            'description': 'Datos de contacto obligatorios para gestión de pedidos'
        }),
        ('Dirección Local/Fiscal', {
            'fields': ('direccion_local', 'ciudad', 'provincia', 'codigo_postal', 'pais'),
            'description': 'Datos obligatorios para facturación'
        }),
        ('Dirección de Entrega', {
            'fields': ('tipo_entrega', 'direccion_entrega', 'ciudad_entrega', 'provincia_entrega', 'codigo_postal_entrega', 'ventana_entrega', 'observaciones_entrega'),
            'description': 'Datos obligatorios para la entrega de pedidos'
        }),
        ('Control de Perfil Operativo', {
            'fields': ('profile_completed', 'items_count'),
            'description': 'Estado y métricas del perfil operativo',
            'classes': ('collapse',)
        }),
        ('Sistema', {
            'fields': ('role', 'status', 'language', 'timezone')
        }),
        ('Estado', {
            'fields': ('is_active', 'is_staff', 'email_verified', 'pending_approval')
        }),
        ('Permisos', {
            'fields': ('is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('last_login', 'last_login_at', 'last_login_ip', 'date_joined', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Aprobación', {
            'fields': ('approved_by', 'approved_at'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
        ('Datos Personales', {
            'fields': ('first_name', 'last_name', 'full_name', 'phone')
        }),
        ('Sistema', {
            'fields': ('role', 'status', 'language', 'company')
        }),
        ('Opciones', {
            'fields': ('is_active', 'is_staff', 'email_verified')
        }),
    )
    
    def profile_completed_badge(self, obj):
        """Muestra badge visual del estado del perfil operativo"""
        if obj.profile_completed:
            return format_html(
                '<span style="padding: 3px 10px; background-color: #dcfce7; color: #166534; border-radius: 12px; font-size: 11px; font-weight: 600;">'
                '✓ Completo'
                '</span>'
            )
        else:
            missing = len(obj.missing_fields)
            return format_html(
                '<span style="padding: 3px 10px; background-color: #fef2f2; color: #991b1b; border-radius: 12px; font-size: 11px; font-weight: 600;">'
                '⚠ Incompleto ({} campos)'
                '</span>',
                missing
            )
    profile_completed_badge.short_description = 'Perfil Operativo'


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('token', 'created_at', 'expires_at')
    ordering = ('-created_at',)


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ['user', 'theme', 'language', 'email_notifications', 'platform_notifications', 'updated_at']
    list_filter = ['theme', 'language', 'email_notifications', 'platform_notifications', 'ai_detail_level']
    search_fields = ['user__email']
    raw_id_fields = ['user']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Interfaz', {
            'fields': ('theme', 'language', 'timezone')
        }),
        ('Notificaciones', {
            'fields': ('email_notifications', 'platform_notifications', 'marketing_emails')
        }),
        ('Preferencias IA', {
            'fields': ('ai_language', 'ai_detail_level', 'ai_format')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SecuritySettings)
class SecuritySettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'two_factor_enabled', 'two_factor_method', 'max_concurrent_sessions', 'password_changed_at']
    list_filter = ['two_factor_enabled', 'two_factor_method']
    search_fields = ['user__email']
    raw_id_fields = ['user']
    readonly_fields = ['api_token_created_at', 'api_token_last_used', 'password_changed_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Autenticación de Dos Factores', {
            'fields': ('two_factor_enabled', 'two_factor_method', 'two_factor_secret')
        }),
        ('API Token', {
            'fields': ('api_token', 'api_token_created_at', 'api_token_last_used'),
            'classes': ('collapse',)
        }),
        ('Sesiones', {
            'fields': ('max_concurrent_sessions', 'session_timeout_minutes')
        }),
        ('Contraseña', {
            'fields': ('password_changed_at', 'password_expires_at')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_info', 'ip_address', 'is_active', 'last_activity', 'expires_at']
    list_filter = ['device_type', 'is_active', 'created_at']
    search_fields = ['user__email', 'ip_address', 'browser', 'os']
    raw_id_fields = ['user']
    readonly_fields = ['session_key', 'created_at', 'last_activity']
    ordering = ['-last_activity']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'session_key', 'is_active')
        }),
        ('Dispositivo', {
            'fields': ('device_type', 'browser', 'os', 'user_agent')
        }),
        ('Conexión', {
            'fields': ('ip_address',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'last_activity', 'expires_at')
        }),
    )
    
    def device_info(self, obj):
        return f"{obj.device_type} - {obj.browser} ({obj.os})"
    device_info.short_description = 'Dispositivo'


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'success_icon', 'ip_address', 'location', 'created_at']
    list_filter = ['success', 'created_at']
    search_fields = ['user__email', 'ip_address', 'location']
    raw_id_fields = ['user']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'success', 'failure_reason')
        }),
        ('Conexión', {
            'fields': ('ip_address', 'location', 'user_agent')
        }),
        ('Fecha', {
            'fields': ('created_at',)
        }),
    )
    
    def success_icon(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✓ Exitoso</span>')
        return format_html('<span style="color: red;">✗ Fallido</span>')
    success_icon.short_description = 'Estado'


@admin.register(ProfileAuditLog)
class ProfileAuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'field_changed', 'ip_address', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__email', 'field_changed', 'ip_address']
    raw_id_fields = ['user']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'action')
        }),
        ('Cambios', {
            'fields': ('field_changed', 'old_value', 'new_value')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Fecha', {
            'fields': ('created_at',)
        }),
    )
