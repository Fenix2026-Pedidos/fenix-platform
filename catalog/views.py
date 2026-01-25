from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.utils import translation
from core.models import PlatformSettings
from .models import Product


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
