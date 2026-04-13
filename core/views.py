from django.contrib.auth.decorators import login_required
from django.db.models import Q, CharField
from django.db.models.functions import Cast
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.timesince import timesince
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from accounts.models import User
from catalog.models import Product
from notifications.models import Notification
from orders.models import Order
from .models import ContactLead

MAX_RESULTS = 5
PUBLIC_CONTACT_INFO = {
    'company_name': 'Fenix Distribuciones S.L.',
    'tax_id': 'CIF pendiente',
    'email': 'info@fenixdelamancha.es',
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

def public_contact(request):
    context = {
        'page_heading': _('Contacto'),
        'contact_info': PUBLIC_CONTACT_INFO,
    }
    return render(request, 'public/contact.html', context)


@require_POST
def api_contact_submit(request):
    """Endpoint para procesar el formulario de contacto vía AJAX"""
    try:
        # 1. Honeypot check (anti-spam)
        # Un campo oculto que los bots suelen rellenar
        if request.POST.get('website'):
            return JsonResponse({'success': False, 'message': _('Detección de actividad sospechosa.')}, status=400)

        # 2. Get and validate data
        nombre = request.POST.get('nombre_completo', '').strip()
        email = request.POST.get('email', '').strip()
        empresa = request.POST.get('empresa', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        asunto = request.POST.get('asunto', '').strip()
        mensaje = request.POST.get('mensaje', '').strip()
        acepta_privacidad = request.POST.get('acepta_privacidad') == 'on' or request.POST.get('acepta_privacidad') == 'true'

        errors = {}
        if not nombre:
            errors['nombre_completo'] = _('El nombre es obligatorio.')
        
        if not email:
            errors['email'] = _('El correo electrónico es obligatorio.')
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors['email'] = _('El correo electrónico no es válido.')

        if not mensaje:
            errors['mensaje'] = _('El mensaje no puede estar vacío.')

        if not acepta_privacidad:
            errors['acepta_privacidad'] = _('Debes aceptar la política de privacidad.')

        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)

        # 3. Create Lead
        lead = ContactLead.objects.create(
            nombre_completo=nombre,
            email=email,
            empresa=empresa,
            telefono=telefono,
            asunto=asunto,
            mensaje=mensaje,
            acepta_privacidad=acepta_privacidad,
            acepta_comunicaciones=request.POST.get('acepta_comunicaciones') == 'on' or request.POST.get('acepta_comunicaciones') == 'true',
            ip=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            origen='formulario_contacto_web'
        )

        return JsonResponse({
            'success': True,
            'message': _('Hemos recibido tu solicitud correctamente. Te contactaremos lo antes posible.')
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _('No hemos podido enviar tu solicitud. Inténtalo de nuevo en unos minutos.')
        }, status=500)
