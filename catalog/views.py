from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.utils import translation
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from core.models import PlatformSettings
from .models import Product
from .forms import ProductForm, StockUpdateForm
from accounts.utils import is_manager_or_admin


def get_user_language(user):
    """
    Obtiene el idioma del usuario según prioridad:
    1. user.language (si está autenticado)
    2. platform.default_language (PlatformSettings)
    3. 'es' (fallback)
    """
    if user.is_authenticated and hasattr(user, 'language') and user.language:
        return user.language
    
    try:
        platform = PlatformSettings.get_settings()
        if platform.default_language:
            return platform.default_language
    except Exception:
        pass
    
    return 'es'


def activate_user_language(request, user):
    """
    Activa el idioma del usuario en la sesión actual.
    Prioridad: user.language -> platform.default_language -> 'es'
    """
    lang = get_user_language(user)
    translation.activate(lang)
    request.LANGUAGE_CODE = lang
    return lang


def product_list(request):
    """Lista de productos del catálogo"""
    products = Product.objects.filter(is_active=True).order_by('-created_at')
    
    # Búsqueda
    search_query = request.GET.get('q', '')
    if search_query:
        products = products.filter(
            Q(name_es__icontains=search_query) |
            Q(name_zh_hans__icontains=search_query) |
            Q(description_es__icontains=search_query) |
            Q(description_zh_hans__icontains=search_query)
        )
    
    lang = get_user_language(request.user)
    
    # Obtener carrito para pasar cantidades iniciales al frontend
    from orders.views import get_cart
    cart = get_cart(request)
    
    # Asegurar que cart es un diccionario válido (json_script lo convertirá a JSON)
    if not cart or not isinstance(cart, dict):
        cart = {}
    
    context = {
        'products': products,
        'search_query': search_query,
        'lang': lang,
        'cart': cart,  # Pasar carrito como dict, json_script lo convertirá
    }
    return render(request, 'catalog/product_list.html', context)


def product_detail(request, pk):
    """Detalle de un producto"""
    product = get_object_or_404(Product, pk=pk, is_active=True)
    lang = get_user_language(request.user)
    
    context = {
        'product': product,
        'lang': lang,
    }
    return render(request, 'catalog/product_detail.html', context)


# ==================== VISTAS DE GESTIÓN (MANAGER/ADMIN) ====================

@login_required
def product_manage_list(request):
    """Lista de productos para gestión (Manager/Super Admin)"""
    if not is_manager_or_admin(request.user):
        messages.error(request, _('No tienes permiso para acceder a esta página.'))
        return redirect('catalog:product_list')
    
    products = Product.objects.all().order_by('-created_at')
    
    # Filtros
    status = request.GET.get('status')
    if status == 'active':
        products = products.filter(is_active=True)
    elif status == 'inactive':
        products = products.filter(is_active=False)
    
    stock_status = request.GET.get('stock')
    if stock_status:
        products = products.filter(stock_status=stock_status)
    
    search = request.GET.get('q')
    if search:
        products = products.filter(
            Q(name_es__icontains=search) |
            Q(name_zh_hans__icontains=search)
        )
    
    context = {
        'products': products,
        'status_filter': status,
        'stock_filter': stock_status,
        'search_query': search,
    }
    return render(request, 'catalog/product_manage_list.html', context)


@login_required
def product_create(request):
    """Crear nuevo producto (Manager/Super Admin)"""
    if not is_manager_or_admin(request.user):
        messages.error(request, _('No tienes permiso para acceder a esta página.'))
        return redirect('catalog:product_list')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, _('Producto creado exitosamente.'))
            return redirect('catalog:product_manage_detail', pk=product.pk)
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'action': 'create',
    }
    return render(request, 'catalog/product_form.html', context)


@login_required
def product_edit(request, pk):
    """Editar producto existente (Manager/Super Admin)"""
    if not is_manager_or_admin(request.user):
        messages.error(request, _('No tienes permiso para acceder a esta página.'))
        return redirect('catalog:product_list')
    
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, _('Producto actualizado exitosamente.'))
            return redirect('catalog:product_manage_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'action': 'edit',
    }
    return render(request, 'catalog/product_form.html', context)


@login_required
def product_manage_detail(request, pk):
    """Detalle de producto para gestión (Manager/Super Admin)"""
    if not is_manager_or_admin(request.user):
        messages.error(request, _('No tienes permiso para acceder a esta página.'))
        return redirect('catalog:product_list')
    
    product = get_object_or_404(Product, pk=pk)
    
    context = {
        'product': product,
    }
    return render(request, 'catalog/product_manage_detail.html', context)


@login_required
def product_delete(request, pk):
    """Eliminar (desactivar) producto (Manager/Super Admin)"""
    if not is_manager_or_admin(request.user):
        messages.error(request, _('No tienes permiso para realizar esta acción.'))
        return redirect('catalog:product_list')
    
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product.is_active = False
        product.save()
        messages.success(request, _('Producto desactivado exitosamente.'))
        return redirect('catalog:product_manage_list')
    
    context = {
        'product': product,
    }
    return render(request, 'catalog/product_confirm_delete.html', context)


@login_required
def product_stock_update(request, pk):
    """Actualizar stock de producto (Manager/Super Admin)"""
    if not is_manager_or_admin(request.user):
        messages.error(request, _('No tienes permiso para realizar esta acción.'))
        return redirect('catalog:product_list')
    
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = StockUpdateForm(request.POST)
        if form.is_valid():
            adjustment = form.cleaned_data['adjustment']
            product.stock_available += adjustment
            product.save()
            messages.success(
                request,
                _('Stock actualizado: %(adj)s. Nuevo stock: %(stock)s') % {
                    'adj': adjustment,
                    'stock': product.stock_available
                }
            )
            return redirect('catalog:product_manage_detail', pk=product.pk)
    else:
        form = StockUpdateForm()
    
    context = {
        'form': form,
        'product': product,
    }
    return render(request, 'catalog/product_stock_update.html', context)

