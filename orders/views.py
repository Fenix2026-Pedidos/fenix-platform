from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
import json

from .models import Order, OrderItem, OrderEvent, OrderDocument
from .forms import OrderStatusUpdateForm, OrderETAForm, OrderDocumentForm
from catalog.models import Product
from accounts.utils import is_manager_or_admin


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
    """Añade un producto al carrito (SUMA a cantidad existente)"""
    try:
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        quantity = int(data.get('quantity', 1))
        
        product = get_object_or_404(Product, pk=product_id, is_active=True)
        
        cart = get_cart(request)
        current_quantity = cart.get(product_id, 0)
        new_quantity = current_quantity + quantity
        cart[product_id] = new_quantity
        save_cart(request, cart)
        
        # Obtener idioma del usuario para el mensaje
        lang = request.user.language if request.user.is_authenticated else 'es'
        product_name = product.name_zh_hans if lang == 'zh-hans' else product.name_es
        
        if lang == 'zh-hans':
            message = f'{product_name} 已添加到购物车'
        else:
            message = f'{product_name} añadido al carrito'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'product_quantity': new_quantity,  # Cantidad total del producto en cesta
            'cart_count': sum(cart.values())   # Total de items en cesta
        })
    except Exception as e:
        error_msg = _('Error al añadir producto al carrito')
        return JsonResponse({'success': False, 'message': error_msg}, status=400)


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
        error_msg = _('Error al actualizar el carrito')
        return JsonResponse({'success': False, 'message': error_msg}, status=400)


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
    
    messages.success(request, _('Pedido #%(id)s creado exitosamente.') % {'id': order.id})
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
    """
    Detalle de un pedido.
    - Cliente: solo puede ver sus propios pedidos
    - Manager/Super Admin: pueden ver cualquier pedido
    """
    if is_manager_or_admin(request.user):
        # Managers y Super Admin pueden ver cualquier pedido
        order = get_object_or_404(Order, pk=pk)
    else:
        # Clientes solo pueden ver sus propios pedidos
        order = get_object_or_404(Order, pk=pk, customer=request.user)
    
    # Obtener documentos del pedido
    documents = order.documents.all()
    
    context = {
        'order': order,
        'items': order.items.all(),
        'events': order.events.all(),
        'documents': documents,
        'is_manager': is_manager_or_admin(request.user),
    }
    return render(request, 'orders/order_detail.html', context)


# ==================== VISTAS DE GESTIÓN (MANAGER/ADMIN) ====================

@login_required
def order_manage_list(request):
    """Lista de todos los pedidos para gestión (Manager/Super Admin)"""
    if not is_manager_or_admin(request.user):
        messages.error(request, _('No tienes permiso para acceder a esta página.'))
        return redirect('orders:order_list')
    
    orders = Order.objects.all().select_related('customer').order_by('-created_at')
    
    # Filtros
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    search = request.GET.get('q')
    if search:
        orders = orders.filter(
            customer__email__icontains=search
        ) | orders.filter(
            customer__full_name__icontains=search
        )
    
    context = {
        'orders': orders,
        'status_filter': status,
        'search_query': search,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'orders/order_manage_list.html', context)


@login_required
@transaction.atomic
def order_update_status(request, pk):
    """Actualizar estado de un pedido (Manager/Super Admin)"""
    if not is_manager_or_admin(request.user):
        messages.error(request, _('No tienes permiso para realizar esta acción.'))
        return redirect('orders:order_list')
    
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        form = OrderStatusUpdateForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            note = form.cleaned_data['note']
            
            # Descontar stock si pasa a "Preparando" por primera vez
            if new_status == Order.STATUS_PREPARING and not order.stock_deducted:
                for item in order.items.all():
                    product = item.product
                    if product.stock_available >= item.quantity:
                        product.stock_available -= item.quantity
                        product.save()
                    else:
                        messages.warning(
                            request,
                            _('Stock insuficiente para %(product)s. Stock disponible: %(stock)s, requerido: %(qty)s') % {
                                'product': product.name_es,
                                'stock': product.stock_available,
                                'qty': item.quantity
                            }
                        )
                order.stock_deducted = True
            
            # Actualizar estado del pedido
            order.status = new_status
            order.save()
            
            # Registrar evento
            OrderEvent.objects.create(
                order=order,
                status=new_status,
                note=note,
                created_by=request.user
            )
            
            messages.success(request, _('Estado del pedido actualizado exitosamente.'))
            return redirect('orders:order_detail', pk=order.pk)
    else:
        form = OrderStatusUpdateForm(initial={'status': order.status})
    
    context = {
        'form': form,
        'order': order,
    }
    return render(request, 'orders/order_update_status.html', context)


@login_required
def order_update_eta(request, pk):
    """Actualizar ETA (fechas estimadas) de un pedido (Manager/Super Admin)"""
    if not is_manager_or_admin(request.user):
        messages.error(request, _('No tienes permiso para realizar esta acción.'))
        return redirect('orders:order_list')
    
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        form = OrderETAForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            
            # Registrar evento
            OrderEvent.objects.create(
                order=order,
                status=order.status,
                note=_('ETA actualizado: %(start)s - %(end)s') % {
                    'start': order.eta_start.strftime('%Y-%m-%d %H:%M') if order.eta_start else 'N/A',
                    'end': order.eta_end.strftime('%Y-%m-%d %H:%M') if order.eta_end else 'N/A',
                },
                created_by=request.user
            )
            
            messages.success(request, _('ETA actualizado exitosamente.'))
            return redirect('orders:order_detail', pk=order.pk)
    else:
        form = OrderETAForm(instance=order)
    
    context = {
        'form': form,
        'order': order,
    }
    return render(request, 'orders/order_update_eta.html', context)


@login_required
def order_dashboard(request):
    """Dashboard de gestión de pedidos (Manager/Super Admin)"""
    if not is_manager_or_admin(request.user):
        messages.error(request, _('No tienes permiso para acceder a esta página.'))
        return redirect('catalog:product_list')
    
    # Estadísticas
    from django.db.models import Count, Sum
    from accounts.models import User
    
    total_orders = Order.objects.count()
    new_orders = Order.objects.filter(status=Order.STATUS_NEW).count()
    preparing_orders = Order.objects.filter(status=Order.STATUS_PREPARING).count()
    pending_users = User.objects.filter(pending_approval=True, is_active=True).count()
    
    # Pedidos recientes
    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:10]
    
    # Productos con bajo stock
    from catalog.models import Product
    low_stock_products = Product.objects.filter(
        stock_status__in=[Product.STOCK_LOW, Product.STOCK_OUT],
        is_active=True
    )[:10]
    
    context = {
        'total_orders': total_orders,
        'new_orders': new_orders,
        'preparing_orders': preparing_orders,
        'pending_users': pending_users,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
    }
    return render(request, 'orders/order_dashboard.html', context)


@login_required
def order_document_upload(request, pk):
    """Subir un documento a un pedido (Manager/Super Admin)"""
    if not is_manager_or_admin(request.user):
        messages.error(request, _('No tienes permiso para realizar esta acción.'))
        return redirect('orders:order_list')
    
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        form = OrderDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.order = order
            document.uploaded_by = request.user
            document.save()
            
            messages.success(request, _('Documento subido exitosamente.'))
            return redirect('orders:order_detail', pk=order.pk)
    else:
        form = OrderDocumentForm()
    
    context = {
        'form': form,
        'order': order,
    }
    return render(request, 'orders/order_document_upload.html', context)


@login_required
def order_document_delete(request, pk, doc_id):
    """Eliminar un documento de un pedido (Manager/Super Admin)"""
    if not is_manager_or_admin(request.user):
        messages.error(request, _('No tienes permiso para realizar esta acción.'))
        return redirect('orders:order_list')
    
    order = get_object_or_404(Order, pk=pk)
    document = get_object_or_404(OrderDocument, pk=doc_id, order=order)
    
    if request.method == 'POST':
        document.file.delete()  # Eliminar archivo físico
        document.delete()
        messages.success(request, _('Documento eliminado exitosamente.'))
        return redirect('orders:order_detail', pk=order.pk)
    
    context = {
        'order': order,
        'document': document,
    }
    return render(request, 'orders/order_document_confirm_delete.html', context)


