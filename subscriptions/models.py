from django.db import models

from organizations.models import Organization


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class Subscription(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_PAST_DUE = 'past_due'
    STATUS_CANCELLED = 'cancelled'
    STATUS_PAUSED = 'paused'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Activa'),
        (STATUS_PAST_DUE, 'Vencida'),
        (STATUS_CANCELLED, 'Cancelada'),
        (STATUS_PAUSED, 'Pausada'),
    ]

    organization = models.OneToOneField(
        Organization,
        on_delete=models.PROTECT,
        related_name='subscription',
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    current_period_start = models.DateField()
    current_period_end = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'{self.organization_id} - {self.status}'
