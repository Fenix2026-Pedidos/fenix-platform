from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator, Page
from decimal import Decimal
import json
from datetime import datetime, date, timedelta
from calendar import monthrange

from .models import Order, OrderItem, OrderEvent, OrderDocument
from .forms import OrderStatusUpdateForm, OrderETAForm, OrderDocumentForm
from catalog.models import Product
from accounts.models import User
from accounts.utils import is_manager_or_admin
from .services import enqueue_order_confirmation_email


# ============================================================
# Utility Functions for Orders
# ============================================================

def get_orders_month_year_data(queryset):
    """
    Extrae meses y años únicos disponibles del queryset de orders
    Retorna: (months, years, months_with_year)
    """
    from django.db.models.functions import TruncMonth
    
    dates = queryset.annotate(month_date=TruncMonth('created_at')).values_list(
        'month_date', flat=True
    ).distinct().order_by('-month_date')
    
    months_with_year = []
    years_set = set()
    
    months_labels = {
        1: _('Enero'),
        2: _('Febrero'),
        3: _('Marzo'),
        4: _('Abril'),
        5: _('Mayo'),
        6: _('Junio'),
        7: _('Julio'),
        8: _('Agosto'),
        9: _('Septiembre'),
        10: _('Octubre'),
        11: _('Noviembre'),
        12: _('Diciembre'),
    }
    
    for dt in dates:
        if dt:
            year = dt.year
            month = dt.month
            years_set.add(year)
            months_with_year.append({
                'value': f'{year}-{month:02d}',
                'label': f'{months_labels[month]} {year}'
            })
    
    years = sorted(list(years_set), reverse=True)
    
    return months_with_year, years


def get_month_label(month_str):
    """
    Convierte formato YYYY-MM a etiqueta legible 'Mes YYYY-MM'
    """
    if not month_str:
        return None
    
    try:
        year, month = map(int, month_str.split('-'))
        months_labels = {
            1: _('Enero'),
            2: _('Febrero'),
            3: _('Marzo'),
            4: _('Abril'),
            5: _('Mayo'),
            6: _('Junio'),
            7: _('Julio'),
            8: _('Agosto'),
            9: _('Septiembre'),
            10: _('Octubre'),
            11: _('Noviembre'),
            12: _('Diciembre'),
        }
        return f"{months_labels[month]} {year}"
    except (ValueError, IndexError, KeyError):
        return None


def filter_orders_by_month_year(queryset, month=None, year=None):
    """
    Filtra queryset por mes y año si se proporcionan
    month: formato 'MM' (01-12) o 'YYYY-MM'
    year: formato 'YYYY'
    """
    if month and len(month) == 7:  # Formato YYYY-MM
        try:
            y, m = map(int, month.split('-'))
            queryset = queryset.filter(created_at__year=y, created_at__month=m)
        except (ValueError, IndexError):
            pass
    elif month and year:  # Formatos separados
        try:
            m = int(month)
            y = int(year)
            queryset = queryset.filter(created_at__year=y, created_at__month=m)
        except ValueError:
            pass
    elif year:
        try:
            y = int(year)
            queryset = queryset.filter(created_at__year=y)
        except ValueError:
            pass
    
    return queryset


# ============================================================
# Cart Functions
# ============================================================

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
    
    # Verificar que el perfil operativo esté completo
    if not request.user.check_profile_completed():
        messages.error(
            request,
            _('Debes completar tu perfil operativo antes de crear un pedido. '
              'Campos faltantes: %(missing_fields)s') % {
                'missing_fields': ', '.join(request.user.missing_fields)
            }
        )
        return redirect('accounts:operative_profile_edit')
    
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

    transaction.on_commit(lambda: enqueue_order_confirmation_email(order.id))
    
    # Limpiar el carrito
    request.session['cart'] = {}
    request.session.modified = True
    
    messages.success(request, _('Pedido #%(id)s creado exitosamente.') % {'id': order.id})
    return redirect('orders:order_detail', pk=order.pk)


@login_required
def order_list(request):
    """
    Vista unificada de pedidos con paginación y filtros.
    
    Comportamiento:
    - Clientes: ven solo sus pedidos con filtros por mes/año
    - Admin/Manager: ven vista agregada por cliente (últimos meses)
    
    Parámetros GET:
    - month: formato YYYY-MM para filtrar por mes
    - year: formato YYYY para filtrar por año
    - page: número de página (por defecto 1)
    - per_page: items por página (10, 25, 50; por defecto 10)
    - client_id: (admin solo) ID de cliente para filtro
    """
    user = request.user
    is_admin = is_manager_or_admin(user)
    
    # Parámetros de paginación y filtros
    selected_month = request.GET.get('month', '')
    selected_year = request.GET.get('year', str(timezone.now().year))
    per_page = request.GET.get('per_page', 10)
    current_page = request.GET.get('page', 1)
    
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    
    # Construct querystring for pagination links
    querystring_parts = []
    if selected_month:
        querystring_parts.append(f'month={selected_month}')
    if selected_year:
        querystring_parts.append(f'year={selected_year}')
    if per_page != 10:
        querystring_parts.append(f'per_page={per_page}')
    querystring = '&' + '&'.join(querystring_parts) if querystring_parts else ''
    
    # ====================================================================
    # VISTA USUARIO: Pedidos personales con filtros por mes/año
    # ====================================================================
    if not is_admin:
        # Obtener pedidos del usuario
        orders_qs = Order.objects.filter(customer=user).select_related('customer')
        
        # Aplicar filtros
        orders_qs = filter_orders_by_month_year(orders_qs, month=selected_month, year=selected_year)
        
        # Ordenar por fecha descendente
        orders_qs = orders_qs.order_by('-created_at')
        
        # Obtener datos para dropdown de meses
        user_orders = Order.objects.filter(customer=user)
        months_available, years_available = get_orders_month_year_data(user_orders)
        
        # Contar total de pedidos en el rango
        total_count = orders_qs.count()
        
        # Etiqueta del mes seleccionado
        month_label = get_month_label(selected_month) if selected_month else _('Todos')
        
        # Paginación
        paginator = Paginator(orders_qs, per_page)
        try:
            page_obj = paginator.page(current_page)
        except:
            page_obj = paginator.page(1)
        
        context = {
            'page_obj': page_obj,
            'paginator': paginator,
            'orders': page_obj.object_list,  # Para compatibilidad con templates antiguos
            'is_admin_view': False,
            'is_manager': False,  # Para compatibilidad
            'client_name': user.full_name or user.email,
            'month_label': month_label,
            'total_count': total_count,
            'selected_month': selected_month,
            'selected_year': selected_year,
            'months_available': months_available,
            'years_available': years_available,
            'per_page': per_page,
            'querystring': querystring,
        }
        
        return render(request, 'orders/order_list.html', context)
    
    # ====================================================================
    # VISTA ADMIN: Pedidos de todos con opciones de filtrado
    # ====================================================================
    else:
        client_id = request.GET.get('client_id')
        
        # Obtener base de pedidos
        orders_qs = Order.objects.all().select_related('customer')
        
        # Filtrar por cliente si se especifica
        if client_id:
            try:
                orders_qs = orders_qs.filter(customer_id=int(client_id))
                client_name = get_object_or_404(User, pk=client_id)
                client_name = client_name.full_name or client_name.email
            except (ValueError, User.DoesNotExist):
                client_id = None
                client_name = _('Todos los clientes')
        else:
            client_name = _('Todos los clientes')
        
        # Aplicar filtros de mes/año
        orders_qs = filter_orders_by_month_year(orders_qs, month=selected_month, year=selected_year)
        
        # Ordenar por fecha descendente
        orders_qs = orders_qs.order_by('-created_at')
        
        # Obtener datos para dropdowns
        all_orders = Order.objects.all()
        months_available, years_available = get_orders_month_year_data(all_orders)
        
        # Clientes disponibles (con pedidos)
        clients = User.objects.filter(orders__isnull=False).distinct().order_by('email')
        
        # Contar total de pedidos en el rango
        total_count = orders_qs.count()
        
        # Etiqueta del mes seleccionado
        month_label = get_month_label(selected_month) if selected_month else _('Todos')
        
        # Paginación
        paginator = Paginator(orders_qs, per_page)
        try:
            page_obj = paginator.page(current_page)
        except:
            page_obj = paginator.page(1)
        
        # Construir querystring incluyendo filtro de cliente si existe
        querystring_parts = []
        if client_id:
            querystring_parts.append(f'client_id={client_id}')
        if selected_month:
            querystring_parts.append(f'month={selected_month}')
        if selected_year:
            querystring_parts.append(f'year={selected_year}')
        if per_page != 10:
            querystring_parts.append(f'per_page={per_page}')
        querystring = '&' + '&'.join(querystring_parts) if querystring_parts else ''
        
        context = {
            'page_obj': page_obj,
            'paginator': paginator,
            'orders': page_obj.object_list,  # Para compatibilidad
            'is_admin_view': True,
            'is_manager': True,  # Para compatibilidad
            'client_name': client_name,
            'month_label': month_label,
            'total_count': total_count,
            'selected_month': selected_month,
            'selected_year': selected_year,
            'selected_client': client_id,
            'clients': clients,
            'months_available': months_available,
            'years_available': years_available,
            'per_page': per_page,
            'querystring': querystring,
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
        order = get_object_or_404(Order.objects.select_related('customer'), pk=pk)
    else:
        # Clientes solo pueden ver sus propios pedidos
        order = get_object_or_404(Order.objects.select_related('customer'), pk=pk, customer=request.user)
    
    # Obtener items del pedido con información del producto
    items = OrderItem.objects.filter(order=order).select_related('product')
    
    # Obtener documentos del pedido
    documents = order.documents.all()
    
    # Información del cliente
    customer = order.customer
    
    # Calcular subtotal (en caso de que haya gastos de envío en el futuro)
    subtotal = sum(item.line_total for item in items)
    shipping_cost = 0  # TODO: Implementar gastos de envío si es necesario
    
    is_manager = is_manager_or_admin(request.user)
    can_cancel_user = False
    cancel_disabled_reason = ''
    if not is_manager:
        now = timezone.now()
        if order.status in [Order.STATUS_CANCELLED, Order.STATUS_DELIVERED]:
            can_cancel_user = False
            cancel_disabled_reason = _('El pedido ya no se puede cancelar.')
        elif order.eta_start and order.eta_start - now < timedelta(hours=24):
            can_cancel_user = False
            cancel_disabled_reason = _('No puedes cancelar con menos de 24 horas de antelación.')
        else:
            can_cancel_user = True

    context = {
        'order': order,
        'items': items,
        'customer': customer,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'events': order.events.all(),
        'documents': documents,
        'is_manager': is_manager,
        'can_cancel_user': can_cancel_user,
        'cancel_disabled_reason': cancel_disabled_reason,
    }
    return render(request, 'orders/order_detail.html', context)


@login_required
@require_POST
@transaction.atomic
def order_cancel(request, pk):
    order = get_object_or_404(Order.objects.select_related('customer'), pk=pk)
    is_admin = is_manager_or_admin(request.user)

    if not is_admin and order.customer_id != request.user.id:
        messages.error(request, _('No tienes permiso para cancelar este pedido.'))
        return redirect('orders:order_detail', pk=order.pk)

    if order.status == Order.STATUS_CANCELLED:
        messages.info(request, _('Este pedido ya esta cancelado.'))
        return redirect('orders:order_detail', pk=order.pk)

    if not is_admin:
        now = timezone.now()
        if order.status == Order.STATUS_DELIVERED:
            messages.error(request, _('Este pedido ya fue entregado y no se puede cancelar.'))
            return redirect('orders:order_detail', pk=order.pk)
        if order.eta_start and order.eta_start - now < timedelta(hours=24):
            messages.error(request, _('No puedes cancelar con menos de 24 horas de antelacion.'))
            return redirect('orders:order_detail', pk=order.pk)

    order.status = Order.STATUS_CANCELLED
    order.save()
    OrderEvent.objects.create(
        order=order,
        status=Order.STATUS_CANCELLED,
        note=_('Pedido cancelado'),
        created_by=request.user,
    )
    messages.success(request, _('Pedido cancelado correctamente.'))
    return redirect('orders:order_detail', pk=order.pk)


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


