from django.db import models

from accounts.models import User
from catalog.models import Product


class RecurringOrder(models.Model):
    FREQ_DAILY = 'daily'
    FREQ_WEEKLY = 'weekly'
    FREQ_MONTHLY = 'monthly'

    FREQUENCY_CHOICES = [
        (FREQ_DAILY, 'Diaria'),
        (FREQ_WEEKLY, 'Semanal'),
        (FREQ_MONTHLY, 'Mensual'),
    ]

    customer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='recurring_orders',
    )
    is_active = models.BooleanField(default=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    delivery_window_hours = models.PositiveIntegerField(default=24)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'Recurring {self.id} - {self.customer.email}'


class RecurringOrderItem(models.Model):
    recurring_order = models.ForeignKey(
        RecurringOrder,
        on_delete=models.CASCADE,
        related_name='items',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='recurring_items',
    )
    product_name_es = models.CharField(max_length=200)
    product_name_zh_hans = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()

    def __str__(self) -> str:
        return f'{self.product_name_es} x {self.quantity}'
