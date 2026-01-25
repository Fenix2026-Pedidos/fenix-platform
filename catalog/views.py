from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Product


def get_user_language(user):
    """Obtiene el idioma del usuario según prioridad"""
    if user.is_authenticated and hasattr(user, 'language'):
        return user.language
    # TODO: Obtener de PlatformSettings si existe
    return 'es'


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
    
    context = {
        'products': products,
        'search_query': search_query,
        'lang': lang,
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
