from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'full_name', 'role', 'language', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('role', 'language', 'is_active', 'is_staff')
    search_fields = ('email', 'full_name')
    ordering = ('-date_joined',)
    filter_horizontal = ()

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Perfil', {'fields': ('full_name', 'role', 'language')}),
        ('Estado', {'fields': ('is_active', 'is_staff', 'email_verified', 'pending_approval')}),
        ('Permisos', {'fields': ('is_superuser', 'groups', 'user_permissions')}),
        ('Importante', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2'),
        }),
        ('Opciones', {'fields': ('role', 'language', 'is_active', 'is_staff')}),
    )
