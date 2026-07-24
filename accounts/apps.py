from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'
    verbose_name = '6. Cuentas'

    def ready(self):
        # Registro explícito de señales de aislamiento por empresa.
        from . import signals  # noqa: F401
