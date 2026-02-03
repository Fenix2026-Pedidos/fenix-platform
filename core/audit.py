from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User


class AuditLog(models.Model):
    """Registro de auditoría para acciones importantes en el sistema"""
    
    ACTION_USER_LOGIN = 'user_login'
    ACTION_USER_LOGOUT = 'user_logout'
    ACTION_USER_APPROVED = 'user_approved'
    ACTION_USER_REJECTED = 'user_rejected'
    ACTION_ORDER_CREATED = 'order_created'
    ACTION_ORDER_STATUS_CHANGED = 'order_status_changed'
    ACTION_ORDER_ETA_UPDATED = 'order_eta_updated'
    ACTION_PRODUCT_CREATED = 'product_created'
    ACTION_PRODUCT_UPDATED = 'product_updated'
    ACTION_PRODUCT_DELETED = 'product_deleted'
    ACTION_STOCK_UPDATED = 'stock_updated'
    ACTION_DOCUMENT_UPLOADED = 'document_uploaded'
    ACTION_DOCUMENT_DELETED = 'document_deleted'
    
    ACTION_CHOICES = [
        (ACTION_USER_LOGIN, _('Inicio de sesión')),
        (ACTION_USER_LOGOUT, _('Cierre de sesión')),
        (ACTION_USER_APPROVED, _('Usuario aprobado')),
        (ACTION_USER_REJECTED, _('Usuario rechazado')),
        (ACTION_ORDER_CREATED, _('Pedido creado')),
        (ACTION_ORDER_STATUS_CHANGED, _('Estado de pedido cambiado')),
        (ACTION_ORDER_ETA_UPDATED, _('ETA actualizado')),
        (ACTION_PRODUCT_CREATED, _('Producto creado')),
        (ACTION_PRODUCT_UPDATED, _('Producto actualizado')),
        (ACTION_PRODUCT_DELETED, _('Producto eliminado')),
        (ACTION_STOCK_UPDATED, _('Stock actualizado')),
        (ACTION_DOCUMENT_UPLOADED, _('Documento subido')),
        (ACTION_DOCUMENT_DELETED, _('Documento eliminado')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name=_('Usuario')
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        verbose_name=_('Acción')
    )
    description = models.TextField(
        verbose_name=_('Descripción')
    )
    object_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Tipo de objeto'),
        help_text=_('Tipo de modelo afectado (Order, Product, User, etc.)')
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('ID del objeto')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('Dirección IP')
    )
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('User Agent')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha y hora')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Registro de Auditoría')
        verbose_name_plural = _('Registros de Auditoría')
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]
    
    def __str__(self):
        user_str = self.user.email if self.user else 'Sistema'
        return f'{user_str} - {self.get_action_display()} - {self.created_at}'
    
    @classmethod
    def log(cls, user, action, description, object_type='', object_id=None, request=None):
        """Helper method para crear un log de auditoría"""
        ip_address = None
        user_agent = ''
        
        if request:
            # Obtener IP del request
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            # Obtener User Agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
        
        return cls.objects.create(
            user=user,
            action=action,
            description=description,
            object_type=object_type,
            object_id=object_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
