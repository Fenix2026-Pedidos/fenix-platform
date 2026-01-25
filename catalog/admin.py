from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name_es', 'name_zh_hans', 'price', 'stock_available',
        'stock_min_threshold', 'stock_status', 'is_active', 'created_at',
    )
    list_filter = ('stock_status', 'is_active')
    search_fields = ('name_es', 'name_zh_hans')
    readonly_fields = ('stock_status', 'created_at')
    fieldsets = (
        (None, {'fields': ('name_es', 'name_zh_hans', 'description_es', 'description_zh_hans', 'price', 'is_active')}),
        ('Stock (solo managers)', {'fields': ('stock_available', 'stock_min_threshold', 'stock_status')}),
        ('Auditoría', {'fields': ('created_at',)}),
    )
