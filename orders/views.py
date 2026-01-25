from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from decimal import Decimal
import json

from .models import Order, OrderItem
from catalog.models import Product


def get_cart(request):
    """Obtiene el carrito de la sesión"""
    cart = request.session.get('cart', {})
    return cart


def save_cart(request, cart):
    """Guarda el carrito en la sesión"""
    request.session['cart'] = cart
    request.session.modified = True


def cart_view(request):
    """Vista del carrito de compras"""
    cart = get_cart(request)
    cart_items = []
    total = Decimal('0.00')
    
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(pk=product_id, is_active=True)
            item_total = product.price * Decimal(quantity)
            total += item_total
            cart_items.append({
                'product': product,
                'quantity': int(quantity),
                'item_total': item_total,
            })
        except Product.DoesNotExist:
            continue
    
    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'orders/cart.html', context)


@require_POST
def cart_add(request):
    """Añade un producto al carrito"""
    try:
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        quantity = int(data.get('quantity', 1))
        
        product = get_object_or_404(Product, pk=product_id, is_active=True)
        
        cart = get_cart(request)
        current_quantity = cart.get(product_id, 0)
        cart[product_id] = current_quantity + quantity
        save_cart(request, cart)
        
        return JsonResponse({
            'success': True,
            'message': f'{product.name_es} añadido al carrito',
            'cart_count': sum(cart.values())
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@require_POST
def cart_remove(request):
    """Elimina un producto del carrito"""
    try:
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        
        cart = get_cart(request)
        if product_id in cart:
            del cart[product_id]
            save_cart(request, cart)
        
        return JsonResponse({
            'success': True,
            'cart_count': sum(cart.values())
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@require_POST
def cart_update(request):
    """Actualiza la cantidad de un producto en el carrito"""
    try:
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        quantity = int(data.get('quantity', 1))
        
        if quantity <= 0:
            return cart_remove(request)
        
        cart = get_cart(request)
        cart[product_id] = quantity
        save_cart(request, cart)
        
        return JsonResponse({
            'success': True,
            'cart_count': sum(cart.values())
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@transaction.atomic
def order_create(request):
    """Crea un nuevo pedido desde el carrito"""
    cart = get_cart(request)
    
    if not cart:
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('orders:cart')
    
    # Crear el pedido
    order = Order.objects.create(
        customer=request.user,
        status=Order.STATUS_NEW,
        total_amount=Decimal('0.00')
    )
    
    total = Decimal('0.00')
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(pk=product_id, is_active=True)
            item = OrderItem.objects.create(
                order=order,
                product=product,
                product_name_es=product.name_es,
                product_name_zh_hans=product.name_zh_hans,
                quantity=int(quantity),
                unit_price=product.price,
            )
            total += item.line_total
        except Product.DoesNotExist:
            continue
    
    order.total_amount = total
    order.save()
    
    # Limpiar el carrito
    request.session['cart'] = {}
    request.session.modified = True
    
    messages.success(request, f'Pedido #{order.id} creado exitosamente.')
    return redirect('orders:order_detail', pk=order.pk)


@login_required
def order_list(request):
    """Lista de pedidos del usuario"""
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'orders/order_list.html', context)


@login_required
def order_detail(request, pk):
    """Detalle de un pedido"""
    order = get_object_or_404(Order, pk=pk, customer=request.user)
    
    context = {
        'order': order,
        'items': order.items.all(),
        'events': order.events.all(),
    }
    return render(request, 'orders/order_detail.html', context)
