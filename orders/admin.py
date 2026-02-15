from django.contrib import admin
from .models import Order, OrderItem, OrderEvent


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ('product',)
    readonly_fields = ('line_total',)
    
    def get_formset(self, request, obj=None, **kwargs):
        formset_class = super().get_formset(request, obj, **kwargs)
        
        class OrderItemFormSet(formset_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Añadir símbolo € a los campos en el inline
                for form in self.forms:
                    if 'unit_price' in form.fields:
                        form.fields['unit_price'].widget.attrs.update({
                            'placeholder': '0.00 €'
                        })
                    if 'line_total' in form.fields:
                        form.fields['line_total'].widget.attrs.update({
                            'placeholder': '0.00 €'
                        })
        
        return OrderItemFormSet


class OrderEventInline(admin.TabularInline):
    model = OrderEvent
    extra = 0
    raw_id_fields = ('created_by',)
    readonly_fields = ('created_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'total_amount', 'delivered_at', 'stock_deducted', 'created_at')
    list_filter = ('status', 'stock_deducted')
    search_fields = ('customer__email', 'customer__full_name')
    readonly_fields = ('total_amount', 'stock_deducted', 'delivered_at', 'created_at', 'updated_at')
    raw_id_fields = ('customer',)
    inlines = (OrderItemInline, OrderEventInline)
    fieldsets = (
        (None, {'fields': ('customer', 'status', 'total_amount', 'stock_deducted')}),
        ('ETA', {'fields': ('eta_start', 'eta_end')}),
        ('Entrega', {'fields': ('delivered_at',)}),
        ('Auditoría', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'unit_price', 'line_total')
    list_filter = ('order__status',)
    search_fields = ('product_name_es', 'product_name_zh_hans')
    raw_id_fields = ('order', 'product')

    class Media:
        js = ('admin/js/orderitem_calc.js',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Añadir símbolo € a unit_price
        form.base_fields['unit_price'].label = 'Unit price (€)'
        form.base_fields['unit_price'].widget.attrs.update({
            'placeholder': '0.00 €'
        })
        
        # Añadir símbolo € a line_total y hacerlo readonly
        form.base_fields['line_total'].label = 'Line total (€)'
        form.base_fields['line_total'].widget.attrs.update({
            'readonly': True,
            'style': 'background-color: #f0f0f0;',
            'placeholder': '0.00 €'
        })
        
        return form


@admin.register(OrderEvent)
class OrderEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'status', 'created_by', 'created_at')
    list_filter = ('status',)
    raw_id_fields = ('order', 'created_by')
    readonly_fields = ('created_at',)
