from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

from .models import RecurringOrder, RecurringOrderItem
from .forms import RecurringOrderForm
from catalog.models import Product
from orders.views import get_cart


@login_required
def recurring_order_list(request):
    """Lista de pedidos recurrentes del usuario"""
    recurring_orders = RecurringOrder.objects.filter(
        customer=request.user
    ).prefetch_related('items').order_by('-created_at')
    
    context = {
        'recurring_orders': recurring_orders,
    }
    return render(request, 'recurring/recurring_order_list.html', context)


@login_required
@transaction.atomic
def recurring_order_create(request):
    """Crear un pedido recurrente desde el carrito"""
    cart = get_cart(request)
    
    if not cart:
        messages.warning(request, _('Tu carrito está vacío.'))
        return redirect('orders:cart')
    
    if request.method == 'POST':
        form = RecurringOrderForm(request.POST)
        if form.is_valid():
            recurring_order = form.save(commit=False)
            recurring_order.customer = request.user
            
            # Calcular next_run_at basado en start_date y frequency
            start_date = form.cleaned_data['start_date']
            recurring_order.next_run_at = timezone.make_aware(
                timezone.datetime.combine(start_date, timezone.datetime.min.time())
            )
            recurring_order.save()
            
            # Agregar items desde el carrito
            for product_id, quantity in cart.items():
                try:
                    product = Product.objects.get(pk=product_id, is_active=True)
                    RecurringOrderItem.objects.create(
                        recurring_order=recurring_order,
                        product=product,
                        product_name_es=product.name_es,
                        product_name_zh_hans=product.name_zh_hans,
                        quantity=int(quantity)
                    )
                except Product.DoesNotExist:
                    continue
            
            # Limpiar carrito
            request.session['cart'] = {}
            request.session.modified = True
            
            messages.success(request, _('Pedido recurrente creado exitosamente.'))
            return redirect('recurring:recurring_order_detail', pk=recurring_order.pk)
    else:
        form = RecurringOrderForm()
    
    # Preparar items del carrito para mostrar
    cart_items = []
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(pk=product_id, is_active=True)
            cart_items.append({
                'product': product,
                'quantity': int(quantity),
            })
        except Product.DoesNotExist:
            continue
    
    context = {
        'form': form,
        'cart_items': cart_items,
    }
    return render(request, 'recurring/recurring_order_create.html', context)


@login_required
def recurring_order_detail(request, pk):
    """Detalle de un pedido recurrente"""
    recurring_order = get_object_or_404(
        RecurringOrder,
        pk=pk,
        customer=request.user
    )
    
    context = {
        'recurring_order': recurring_order,
        'items': recurring_order.items.all(),
    }
    return render(request, 'recurring/recurring_order_detail.html', context)


@login_required
def recurring_order_toggle(request, pk):
    """Activar/desactivar un pedido recurrente"""
    recurring_order = get_object_or_404(
        RecurringOrder,
        pk=pk,
        customer=request.user
    )
    
    if request.method == 'POST':
        recurring_order.is_active = not recurring_order.is_active
        recurring_order.save()
        
        if recurring_order.is_active:
            messages.success(request, _('Pedido recurrente activado.'))
        else:
            messages.success(request, _('Pedido recurrente desactivado.'))
        
        return redirect('recurring:recurring_order_detail', pk=recurring_order.pk)
    
    context = {
        'recurring_order': recurring_order,
    }
    return render(request, 'recurring/recurring_order_toggle.html', context)


@login_required
def recurring_order_delete(request, pk):
    """Eliminar un pedido recurrente"""
    recurring_order = get_object_or_404(
        RecurringOrder,
        pk=pk,
        customer=request.user
    )
    
    if request.method == 'POST':
        recurring_order.delete()
        messages.success(request, _('Pedido recurrente eliminado.'))
        return redirect('recurring:recurring_order_list')
    
    context = {
        'recurring_order': recurring_order,
    }
    return render(request, 'recurring/recurring_order_confirm_delete.html', context)

