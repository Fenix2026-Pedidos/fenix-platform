from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Company, UserCompany, Organization


@admin.register(Company)
class CompanyAdmin(SimpleHistoryAdmin):
    list_display = ['name', 'vat_number', 'sector', 'size', 'country', 'city', 'is_active', 'created_at']
    list_filter = ['sector', 'size', 'country', 'is_active', 'created_at']
    search_fields = ['name', 'vat_number', 'email', 'city']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['uuid', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'slug', 'uuid', 'logo', 'is_active')
        }),
        ('Datos Fiscales', {
            'fields': ('vat_number', 'tax_id')
        }),
        ('Clasificación', {
            'fields': ('sector', 'size')
        }),
        ('Ubicación', {
            'fields': ('country', 'city', 'address', 'postal_code')
        }),
        ('Contacto', {
            'fields': ('phone', 'email', 'website')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserCompany)
class UserCompanyAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'job_title', 'department', 'is_company_admin', 'is_active', 'joined_at']
    list_filter = ['is_company_admin', 'is_billing_contact', 'is_active', 'joined_at']
    search_fields = ['user__email', 'company__name', 'job_title', 'department']
    raw_id_fields = ['user', 'company']
    readonly_fields = ['joined_at', 'left_at']
    
    fieldsets = (
        ('Relación', {
            'fields': ('user', 'company', 'is_active')
        }),
        ('Rol en la Empresa', {
            'fields': ('job_title', 'department')
        }),
        ('Permisos', {
            'fields': ('is_company_admin', 'is_billing_contact')
        }),
        ('Fechas', {
            'fields': ('joined_at', 'left_at')
        }),
    )


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin para el modelo legacy Organization"""
    list_display = ['name', 'default_language', 'is_active', 'created_at']
    list_filter = ['default_language', 'is_active']
    search_fields = ['name']
