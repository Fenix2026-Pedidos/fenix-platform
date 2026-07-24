from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from accounts.models import User
from catalog.models import Product


class RecurringOrder(models.Model):
    FREQ_DAILY = 'daily'
    FREQ_WEEKLY = 'weekly'
    FREQ_MONTHLY = 'monthly'

    FREQUENCY_CHOICES = [
        (FREQ_DAILY, _('Diaria')),
        (FREQ_WEEKLY, _('Semanal')),
        (FREQ_MONTHLY, _('Mensual')),
    ]

    customer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='recurring_orders',
        verbose_name=_('Cliente')
    )
    organization = models.ForeignKey(
        'accounts.CustomerOrganization',
        on_delete=models.PROTECT,
        related_name='recurring_orders',
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('Empresa cliente'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Activo'))
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, verbose_name=_('Frecuencia'))
    start_date = models.DateField(verbose_name=_('Fecha Inicio'))
    end_date = models.DateField(null=True, blank=True, verbose_name=_('Fecha Fin'))
    next_run_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Próxima Ejecución'))
    delivery_window_hours = models.PositiveIntegerField(default=24, verbose_name=_('Ventana Entrega (horas)'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha Creación'))

    class Meta:
        verbose_name = _('Pedido Recurrente')
        verbose_name_plural = _('Pedidos Recurrentes')
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['organization', 'is_active'],
                name='recurring_org_active_idx',
            ),
        ]

    def save(self, *args, **kwargs):
        if self.customer_id:
            from accounts.organizations import (
                get_user_customer_membership,
            )

            membership = get_user_customer_membership(self.customer)
            customer_organization = membership.organization
            if self.organization_id is None:
                self.organization = customer_organization
            elif self.organization_id != customer_organization.id:
                raise ValidationError(
                    'El pedido recurrente y su cliente deben pertenecer a la misma empresa.'
                )
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'Recurrente {self.id} - {self.customer.email}'


class RecurringOrderItem(models.Model):
    recurring_order = models.ForeignKey(
        RecurringOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Pedido Recurrente')
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='recurring_items',
        verbose_name=_('Producto')
    )
    product_name_es = models.CharField(max_length=200, verbose_name=_('Nombre (ES)'))
    product_name_zh_hans = models.CharField(max_length=200, verbose_name=_('Nombre (中文)'))
    quantity = models.PositiveIntegerField(verbose_name=_('Cantidad'))

    class Meta:
        verbose_name = _('Línea de Pedido Recurrente')
        verbose_name_plural = _('Líneas de Pedidos Recurrentes')

    @property
    def translated_name(self):
        from django.utils.translation import get_language
        lang = get_language()
        if lang == 'zh-hans':
            return self.product_name_zh_hans or self.product_name_es
        return self.product_name_es

    def __str__(self) -> str:
        return f'{self.product_name_es} x {self.quantity}'
