from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.utils import translation
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
import unicodedata
from core.models import PlatformSettings
from .models import Product, PromotionalProduct
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


def normalize_text(text):
    """
    Normaliza texto: minúsculas + quita diacríticos/tildes.
    Ejemplo: 'Sándwich' -> 'sandwich', 'Jamón' -> 'jamon'
    """
    if not text:
        return ''
    nfkd = unicodedata.normalize('NFKD', str(text).lower().strip())
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def kw_variants(keyword):
    """
    Genera variantes de una keyword: la original y la versión sin tildes.
    Ambas se usan en búsquedas OR para máxima compatibilidad.
    """
    original = keyword.lower().strip()
    normalized = normalize_text(keyword)
    variants = [original]
    if normalized != original:
        variants.append(normalized)
    return variants


def product_list(request):
    """Lista de productos del catálogo"""
    products = Product.objects.filter(is_active=True)
    
    # Obtener productos promocionales activos (máximo 8)
    featured_products = PromotionalProduct.objects.filter(is_active=True).order_by('display_order', '-created_at')[:8]
    
    # ── 1. BÚSQUEDA INTELIGENTE ───────────────────────────────────────────────
    # Normaliza el texto del usuario y extrae tokens.
    # Para cada token genera variante con y sin tildes.
    # Lógica AND entre tokens: el producto debe contener TODOS los tokens.
    search_query = request.GET.get('q', '').strip()
    if search_query:
        tokens = search_query.lower().split()
        for token in tokens:
            token_q = Q()
            for variant in kw_variants(token):
                token_q |= (
                    Q(name_es__icontains=variant) |
                    Q(reference__icontains=variant) |
                    Q(description_es__icontains=variant)
                )
            products = products.filter(token_q)

    # ── 2. FILTRADO POR TIPO DE PRODUCTO ─────────────────────────────────────
    # Mappings basados en los nombres reales de los productos en la BD.
    # Cada lista incluye variantes con y sin tildes para cubrir cualquier texto.
    active_type = request.GET.get('type', 'todos')
    if active_type != 'todos':
        category_mappings = {
            'sandwich': [
                'sándwich', 'sandwich', 'sandw',
            ],
            'salchichas': [
                'salchicha', 'frankfurt', 'salchichón', 'salchichon',
                'big classic', 'big pavo', 'big pollo', 'big queso',
                'viena', 'bratwurst', 'hot dog',
            ],
            'pizzas': [
                'pizza', 'pizzas',
            ],
            'jamon-cocido': [
                'jamón cocido', 'jamon cocido',
                'york', 'cocido', 'fiambre',
            ],
            'jamon-curado': [
                'jamón curado', 'jamon curado',
                'jamón serrano', 'jamon serrano',
                'curado 1954', 'bodega', 'reserva', 'gran reserva',
            ],
            'pavo': [
                'pavo', 'pechuga pavo', 'fiambre pavo',
            ],
            'pollo': [
                'pollo', 'pechuga pollo', 'fiambre pollo',
            ],
            'charcuteria': [
                'mortadela', 'chopped', 'choppep',
                'chorizo', 'salami', 'cervelat', 'cabeza jabalí',
                'bacon', 'lacón', 'lacon', 'panceta',
                'taquito', 'tiras', 'sarta', 'embutido',
                'charcutería', 'charcuteria',
            ],
            'curados': [
                'caña de lomo', 'caña lomo', 'caña',
                'salchichón', 'salchichon',
                'semicurado', 'fuet', 'fuetería', 'fueteria',
                'chorizo curado', 'sarta',
            ],
            'ibericos': [
                'ibérico', 'iberico',
                'bellota', 'pata negra', 'cebo',
            ],
            'fuet': [
                'fuet', 'fuetería', 'fueteria', 'espetec',
            ],
        }

        if active_type in category_mappings:
            keywords = category_mappings[active_type]
            category_q = Q()
            for kw in keywords:
                for variant in kw_variants(kw):
                    category_q |= (
                        Q(name_es__icontains=variant) |
                        Q(description_es__icontains=variant)
                    )
            products = products.filter(category_q)

    # ── 3. FILTRADO POR CARACTERÍSTICAS ESPECIALES ───────────────────────────
    # Lógica AND: el producto debe cumplir TODAS las características marcadas.
    active_features = request.GET.get('features', '')
    feature_list = []
    if active_features:
        feature_list = [f.strip() for f in active_features.split(',') if f.strip()]
        feature_mappings = {
            'sin-lactosa':      ['sin lactosa', 'no lactose', 'lactosa'],
            'sin-conservantes': ['sin conservantes', 'no preservatives', 'conservantes'],
            'sin-colorantes':   ['sin colorantes', 'no artificial colors', 'colorantes'],
            'sin-azucares':     ['sin azucares', 'sin azúcar', 'sin azucar', 'no sugar'],
        }

        for feat in feature_list:
            if feat in feature_mappings:
                keywords = feature_mappings[feat]
                feat_q = Q()
                for kw in keywords:
                    for variant in kw_variants(kw):
                        feat_q |= (
                            Q(name_es__icontains=variant) |
                            Q(description_es__icontains=variant)
                        )
                products = products.filter(feat_q)

    # ── 4. ORDENACIÓN ─────────────────────────────────────────────────────────
    sort_by = request.GET.get('sort', 'relevance')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'name_asc':
        products = products.order_by('name_es')
    elif sort_by == 'name_desc':
        products = products.order_by('-name_es')
    else:
        products = products.order_by('catalog_order', '-created_at')

    # ── 5. PAGINACIÓN ─────────────────────────────────────────────────────────
    try:
        page_size = int(request.GET.get('page_size', 20))
        if page_size not in [20, 40, 60]:
            page_size = 20
    except ValueError:
        page_size = 20

    paginator = Paginator(products, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    lang = get_user_language(request.user)

    # Obtener carrito para pasar cantidades iniciales al frontend
    from orders.views import get_cart
    cart = get_cart(request)

    if not cart or not isinstance(cart, dict):
        cart = {}

    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'search_query': search_query,
        'sort': sort_by,
        'page_size': page_size,
        'active_type': active_type,
        'active_features': feature_list,
        'lang': lang,
        'cart': cart,
        'featured_products': featured_products,
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
            Q(name_zh_hans__icontains=search) |
            Q(reference__icontains=search)
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


@login_required
def update_catalog_order(request):
    """Actualiza el orden de los productos en el catálogo (AJAX)"""
    if not is_manager_or_admin(request.user):
        from django.http import JsonResponse
        return JsonResponse({'status': 'error', 'message': _('Permiso denegado')}, status=403)
    
    if request.method == 'POST':
        import json
        from django.http import JsonResponse
        try:
            data = json.loads(request.body)
            ordered_ids = data.get('ordered_ids', [])
            
            # Actualización masiva eficiente
            for index, product_id in enumerate(ordered_ids):
                Product.objects.filter(id=product_id).update(catalog_order=index + 1)
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    from django.http import JsonResponse
    return JsonResponse({'status': 'error', 'message': _('Método no permitido')}, status=405)
