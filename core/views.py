from django.contrib.auth.decorators import login_required
from django.db.models import Q, CharField
from django.db.models.functions import Cast
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.timesince import timesince
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET

from accounts.models import User
from catalog.models import Product
from notifications.models import Notification
from orders.models import Order

MAX_RESULTS = 5
PUBLIC_CONTACT_INFO = {
    'company_name': 'Fenix Distribuciones S.L.',
    'tax_id': 'CIF pendiente',
    'email': 'info@fenixdistribuciones.com',
    'phone': '+34 600 159 456',
}


def _can_view_all_orders(user: User) -> bool:
    """Determina si el usuario puede ver pedidos de otros usuarios."""
    return (
        user.is_superuser
        or user.is_staff
        or user.role in (User.ROLE_ADMIN, User.ROLE_SUPER_ADMIN)
    )


@login_required
@require_GET
def global_search(request):
    """Endpoint JSON para el buscador inteligente del topbar."""
    query = (request.GET.get('q') or '').strip()
    results = {
        'orders': [],
        'products': [],
        'actions': [],
    }

    if len(query) < 2:
        return JsonResponse({'query': query, 'results': results})

    results['orders'] = _search_orders(query, request.user)
    results['products'] = _search_products(query)
    results['actions'] = _search_notifications(query, request.user, request.LANGUAGE_CODE)

    return JsonResponse({'query': query, 'results': results})


def _search_orders(query: str, user: User) -> list[dict]:
    qs = Order.objects.all()
    if not _can_view_all_orders(user):
        qs = qs.filter(customer=user)

    qs = (
        qs.annotate(id_str=Cast('id', CharField()))
        .filter(
            Q(id_str__icontains=query)
            | Q(customer__full_name__icontains=query)
            | Q(customer__email__icontains=query)
        )
        .select_related('customer')[:MAX_RESULTS]
    )

    return [
        {
            'id': order.id,
            'title': f"{_('Pedido')} #{order.id}",
            'subtitle': f"{order.get_status_display()} • {order.customer.display_name}",
            'url': reverse('orders:order_detail', args=[order.id]),
        }
        for order in qs
    ]


def _search_products(query: str) -> list[dict]:
    qs = Product.objects.filter(is_active=True).filter(
        Q(name_es__icontains=query)
        | Q(name_zh_hans__icontains=query)
        | Q(description_es__icontains=query)
        | Q(description_zh_hans__icontains=query)
    )[:MAX_RESULTS]

    return [
        {
            'id': product.id,
            'title': product.name_es or product.name_zh_hans,
            'subtitle': f"{_('Stock')}: {product.get_stock_status_display()}",
            'url': reverse('catalog:product_detail', args=[product.id]),
        }
        for product in qs
    ]


def _search_notifications(query: str, user: User, language_code: str | None) -> list[dict]:
    lang = (language_code or '').lower()
    subject_field = 'subject_zh_hans' if lang.startswith('zh') else 'subject_es'
    message_field = 'message_zh_hans' if lang.startswith('zh') else 'message_es'

    lookup = Q(**{f'{subject_field}__icontains': query}) | Q(
        **{f'{message_field}__icontains': query}
    )

    qs = (
        Notification.objects.filter(user=user, is_read=False)
        .filter(lookup)
        .order_by('-created_at')[:MAX_RESULTS]
    )

    now = timezone.now()
    subtitle_suffix = _('atrás')

    return [
        {
            'id': notification.id,
            'title': getattr(notification, subject_field),
            'subtitle': f"{timesince(notification.created_at, now)} {subtitle_suffix}",
            'url': reverse('accounts:dashboard'),
        }
        for notification in qs
    ]


def public_about(request):
    context = {
        'page_heading': _('Quiénes somos'),
        'contact_info': PUBLIC_CONTACT_INFO,
    }
    return render(request, 'public/about.html', context)


def public_legal(request):
    context = {
        'page_heading': _('Aviso legal'),
        'contact_info': PUBLIC_CONTACT_INFO,
    }
    return render(request, 'public/legal.html', context)


def public_privacy(request):
    context = {
        'page_heading': _('Política de privacidad'),
        'contact_info': PUBLIC_CONTACT_INFO,
    }
    return render(request, 'public/privacy.html', context)
