"""
Template tags and filters for orders app.
"""
from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.filter
def currency_format(value):
    """
    Formatea un número como moneda EUR
    Uso: {{ amount|currency_format }}
    """
    try:
        return f"{float(value):.2f} €"
    except (ValueError, TypeError):
        return "0.00 €"


@register.filter
def status_badge_class(status):
    """
    Retorna la clase CSS para el badge de estado
    Uso: <span class="status-badge {{ order.status|status_badge_class }}">
    """
    class_map = {
        'new': 'status-new',
        'confirmed': 'status-confirmed',
        'preparing': 'status-preparing',
        'out_for_delivery': 'status-out_for_delivery',
        'delivered': 'status-delivered',
        'cancelled': 'status-cancelled',
    }
    return class_map.get(status, 'status-new')


@register.filter
def status_label(status):
    """
    Retorna la etiqueta de texto para el estado
    Uso: {{ order.status|status_label }}
    """
    labels = {
        'new': _('Nuevo'),
        'confirmed': _('Confirmado'),
        'preparing': _('Preparando'),
        'out_for_delivery': _('En reparto'),
        'delivered': _('Entregado'),
        'cancelled': _('Cancelado'),
    }
    return labels.get(status, status)


@register.simple_tag
def is_status_delivered(status):
    """
    Retorna True si el estado es 'entregado'
    Uso: {% is_status_delivered order.status as is_delivered %}
    """
    return status == 'delivered'


@register.simple_tag
def get_status_color(status):
    """
    Retorna el color HEX para el estado
    Uso: style="color: {% get_status_color order.status %}"
    """
    color_map = {
        'new': '#0c4a6e',  # Blue
        'confirmed': '#312e81',  # Indigo
        'preparing': '#78350f',  # Amber
        'out_for_delivery': '#7c2d12',  # Orange
        'delivered': '#15803d',  # Green
        'cancelled': '#7f1d1d',  # Red
    }
    return color_map.get(status, '#0c4a6e')


@register.simple_tag
def get_status_bg_color(status):
    """
    Retorna el color de fondo HEX para el estado
    Uso: style="background-color: {% get_status_bg_color order.status %}"
    """
    color_map = {
        'new': '#dbeafe',  # Light blue
        'confirmed': '#e0e7ff',  # Light indigo
        'preparing': '#fef3c7',  # Light amber
        'out_for_delivery': '#fed7aa',  # Light orange
        'delivered': '#dcfce7',  # Light green
        'cancelled': '#fee2e2',  # Light red
    }
    return color_map.get(status, '#dbeafe')
