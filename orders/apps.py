from django.apps import AppConfig


class OrdersConfig(AppConfig):
    name = 'orders'
    default_auto_field = 'django.db.models.BigAutoField'
    verbose_name = '2. Pedidos'

    def ready(self):
        import orders.signals  # noqa: F401
