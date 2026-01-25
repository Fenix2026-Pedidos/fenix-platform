from django.contrib import admin
from .models import RecurringOrder, RecurringOrderItem


class RecurringOrderItemInline(admin.TabularInline):
    model = RecurringOrderItem
    extra = 0
    raw_id_fields = ('product',)


@admin.register(RecurringOrder)
class RecurringOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'frequency', 'is_active', 'start_date', 'end_date', 'next_run_at', 'created_at')
    list_filter = ('frequency', 'is_active')
    search_fields = ('customer__email', 'customer__full_name')
    raw_id_fields = ('customer',)
    inlines = (RecurringOrderItemInline,)
    readonly_fields = ('created_at',)


@admin.register(RecurringOrderItem)
class RecurringOrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'recurring_order', 'product', 'quantity')
    list_filter = ('recurring_order__frequency',)
    raw_id_fields = ('recurring_order', 'product')
