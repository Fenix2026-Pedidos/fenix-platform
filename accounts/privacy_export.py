"""Construcción segura de la exportación personal de un usuario.

El esquema es deliberadamente explícito: no se usan ``values()`` sin campos y
no se buscan leads mediante identificadores vacíos o ambiguos.
"""

from django.utils import timezone

from accounts.models import LoginHistory, ProfileAuditLog
from crm.models import CRMLead
from orders.models import Order
from recurring.models import RecurringOrder


PROFILE_FIELDS = (
    'uuid', 'email', 'first_name', 'last_name', 'full_name', 'phone',
    'company', 'job_title', 'vat_number', 'telefono_empresa',
    'telefono_reparto', 'direccion_local', 'ciudad', 'provincia',
    'codigo_postal', 'pais', 'tipo_entrega', 'direccion_entrega',
    'ciudad_entrega', 'provincia_entrega', 'codigo_postal_entrega',
    'ventana_entrega', 'observaciones_entrega', 'language', 'timezone',
    'date_joined', 'updated_at', 'last_login_at',
)
ORDER_FIELDS = (
    'id', 'status', 'eta_start', 'eta_end', 'total_amount', 'delivered_at',
    'created_at', 'updated_at',
)
ORDER_ITEM_FIELDS = (
    'product_name_es', 'product_name_zh_hans', 'quantity', 'unit_price',
    'line_total',
)
ORDER_DOCUMENT_FIELDS = ('id', 'document_type', 'title', 'uploaded_at')
RECURRING_ORDER_FIELDS = (
    'id', 'is_active', 'frequency', 'start_date', 'end_date', 'next_run_at',
    'delivery_window_hours', 'created_at',
)
RECURRING_ITEM_FIELDS = (
    'product_name_es', 'product_name_zh_hans', 'quantity',
)
CRM_FIELDS = (
    'uuid', 'full_name', 'company_name', 'phone', 'email', 'channel',
    'source', 'first_message', 'lead_status', 'validation_status',
    'created_at', 'updated_at',
)
LOGIN_FIELDS = (
    'success', 'failure_reason', 'ip_address', 'user_agent', 'location',
    'created_at',
)
PROFILE_AUDIT_FIELDS = (
    'action', 'field_changed', 'old_value', 'new_value', 'created_at',
)


def _selected(instance, fields):
    return {field: getattr(instance, field, None) for field in fields}


def build_personal_data_export(user):
    """Devuelve únicamente información vinculada inequívocamente al usuario."""
    orders = []
    order_queryset = (
        Order.objects.filter(customer=user)
        .prefetch_related('items', 'documents')
        .order_by('id')
    )
    for order in order_queryset:
        row = _selected(order, ORDER_FIELDS)
        row['items'] = [
            _selected(item, ORDER_ITEM_FIELDS) for item in order.items.all()
        ]
        # Metadatos del documento, nunca su ruta interna o una URL firmada.
        row['documents'] = [
            _selected(document, ORDER_DOCUMENT_FIELDS)
            for document in order.documents.all()
        ]
        orders.append(row)

    recurring_orders = []
    recurring_queryset = (
        RecurringOrder.objects.filter(customer=user)
        .prefetch_related('items')
        .order_by('id')
    )
    for recurring_order in recurring_queryset:
        row = _selected(recurring_order, RECURRING_ORDER_FIELDS)
        row['items'] = [
            _selected(item, RECURRING_ITEM_FIELDS)
            for item in recurring_order.items.all()
        ]
        recurring_orders.append(row)

    # El email de la cuenta es único y verificable. Un teléfono vacío o
    # compartido podría asociar registros de terceros.
    crm_rows = list(
        CRMLead.objects.filter(email__iexact=user.email)
        .values(*CRM_FIELDS)
        .order_by('created_at')
    )

    return {
        'schema_version': '1.0',
        'generated_at': timezone.now(),
        'profile': _selected(user, PROFILE_FIELDS),
        'orders': orders,
        'recurring_orders': recurring_orders,
        'crm': crm_rows,
        'login_history': list(
            LoginHistory.objects.filter(user=user)
            .values(*LOGIN_FIELDS)
            .order_by('created_at')
        ),
        'profile_audit': list(
            ProfileAuditLog.objects.filter(user=user)
            .values(*PROFILE_AUDIT_FIELDS)
            .order_by('created_at')
        ),
    }
