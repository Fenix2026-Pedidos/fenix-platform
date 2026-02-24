from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
import uuid


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.ROLE_SUPER_ADMIN)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('pending_approval', False)
        extra_fields.setdefault('email_verified', True)
        extra_fields.setdefault('status', User.STATUS_ACTIVE)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_SUPER_ADMIN = 'super_admin'
    ROLE_ADMIN = 'admin'
    ROLE_USER = 'user'

    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, _('Super Admin')),
        (ROLE_ADMIN, _('Admin')),
        (ROLE_USER, _('User')),
    ]

    LANGUAGE_ES = 'es'
    LANGUAGE_ZH_HANS = 'zh-hans'

    LANGUAGE_CHOICES = [
        (LANGUAGE_ES, _('Español')),
        (LANGUAGE_ZH_HANS, _('Chinese (Simplified)')),
    ]

    # Status choices para gestión de usuarios
    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_REJECTED = 'rejected'
    STATUS_DISABLED = 'disabled'

    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pendiente')),
        (STATUS_ACTIVE, _('Activo')),
        (STATUS_REJECTED, _('Rechazado')),
        (STATUS_DISABLED, _('Deshabilitado')),
    ]

    # IDENTIFICACIÓN
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)  # unique=True se añade en migración posterior
    email = models.EmailField(unique=True)
    
    # DATOS PERSONALES
    full_name = models.CharField(max_length=200)  # Mantener compatibilidad
    first_name = models.CharField(max_length=100, blank=True, verbose_name=_('Nombre'))
    last_name = models.CharField(max_length=100, blank=True, verbose_name=_('Apellidos'))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_('Teléfono'))
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # EMPRESA (legacy - mantener)
    company = models.CharField(max_length=200, blank=True, default='')
    
    # ============================================================================
    # PERFIL OPERATIVO - Campos obligatorios para realizar pedidos
    # ============================================================================
    
    # CONTACTO
    telefono_empresa = models.CharField(
        max_length=20, 
        blank=True, 
        verbose_name=_('Teléfono empresa'),
        help_text=_('Teléfono de contacto de la empresa')
    )
    telefono_reparto = models.CharField(
        max_length=20, 
        blank=True,  # blank=True para migración, required en formulario
        verbose_name=_('Teléfono reparto'),
        help_text=_('Teléfono de contacto para el reparto (OBLIGATORIO)')
    )
    
    # DIRECCIÓN FISCAL / LOCAL (OBLIGATORIOS)
    direccion_local = models.CharField(
        max_length=300, 
        blank=True, 
        verbose_name=_('Dirección local'),
        help_text=_('Dirección fiscal o del local (OBLIGATORIO)')
    )
    ciudad = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name=_('Ciudad'),
        help_text=_('Ciudad del local (OBLIGATORIO)')
    )
    provincia = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name=_('Provincia'),
        help_text=_('Provincia del local (OBLIGATORIO)')
    )
    codigo_postal = models.CharField(
        max_length=10, 
        blank=True, 
        verbose_name=_('Código postal'),
        help_text=_('Código postal del local (OBLIGATORIO)')
    )
    pais = models.CharField(
        max_length=100, 
        default='España', 
        verbose_name=_('País'),
        help_text=_('País del local')
    )
    
    # DIRECCIÓN DE ENTREGA (OBLIGATORIOS)
    TIPO_ENTREGA_RECOGIDA = 'recogida'
    TIPO_ENTREGA_ENVIO = 'envio'
    
    TIPO_ENTREGA_CHOICES = [
        (TIPO_ENTREGA_RECOGIDA, _('Recogida en local')),
        (TIPO_ENTREGA_ENVIO, _('Envío a domicilio')),
    ]
    
    tipo_entrega = models.CharField(
        max_length=20,
        choices=TIPO_ENTREGA_CHOICES,
        blank=True,
        verbose_name=_('Tipo de entrega'),
        help_text=_('Método de entrega preferido (OBLIGATORIO)')
    )
    direccion_entrega = models.CharField(
        max_length=300, 
        blank=True, 
        verbose_name=_('Dirección de entrega'),
        help_text=_('Dirección donde se realizará la entrega (OBLIGATORIO)')
    )
    ciudad_entrega = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name=_('Ciudad entrega'),
        help_text=_('Ciudad de entrega (OBLIGATORIO)')
    )
    provincia_entrega = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name=_('Provincia entrega'),
        help_text=_('Provincia de entrega (OBLIGATORIO)')
    )
    codigo_postal_entrega = models.CharField(
        max_length=10, 
        blank=True, 
        verbose_name=_('Código postal entrega'),
        help_text=_('Código postal de entrega (OBLIGATORIO)')
    )
    ventana_entrega = models.CharField(
        max_length=200, 
        blank=True, 
        verbose_name=_('Ventana de entrega'),
        help_text=_('Horario o ventana de entrega preferida (opcional)')
    )
    observaciones_entrega = models.TextField(
        blank=True, 
        verbose_name=_('Observaciones de entrega'),
        help_text=_('Instrucciones especiales para la entrega (opcional)')
    )
    
    # CONTEXTO OPERATIVO
    items_count = models.IntegerField(
        default=0, 
        verbose_name=_('Contador de items'),
        help_text=_('Número de items en el perfil operativo')
    )
    
    # CONTROL DE COMPLETITUD
    profile_completed = models.BooleanField(
        default=False,
        verbose_name=_('Perfil completado'),
        help_text=_('Indica si el perfil operativo está completo para realizar pedidos')
    )
    
    # ============================================================================
    # FIN PERFIL OPERATIVO
    # ============================================================================
    
    # SISTEMA
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_USER,
    )
    language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default=LANGUAGE_ES,
    )
    timezone = models.CharField(max_length=50, default='Europe/Madrid', verbose_name=_('Zona horaria'))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        help_text=_('Estado del usuario en el sistema')
    )
    
    # FLAGS
    email_verified = models.BooleanField(default=False)
    pending_approval = models.BooleanField(default=True)  # Mantener por compatibilidad
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # FECHAS
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Último acceso'))
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name=_('IP último acceso'))
    
    # APROBACIÓN
    approved_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_users',
        help_text=_('Usuario que aprobó esta cuenta')
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS: list[str] = ['full_name']
    
    class Meta:
        verbose_name = _('Usuario')
        verbose_name_plural = _('Usuarios')
        ordering = ['-date_joined']

    def __str__(self) -> str:
        return self.email
    
    def get_status_display_class(self):
        """Retorna clase CSS según el status"""
        status_classes = {
            self.STATUS_PENDING: 'warning',
            self.STATUS_ACTIVE: 'success',
            self.STATUS_REJECTED: 'danger',
            self.STATUS_DISABLED: 'secondary',
        }
        return status_classes.get(self.status, 'secondary')
    
    # Métodos helper de roles
    def is_super_admin(self):
        """Verifica si el usuario es Super Admin"""
        return self.role == self.ROLE_SUPER_ADMIN
    
    def is_admin(self):
        """Verifica si el usuario es Admin"""
        return self.role == self.ROLE_ADMIN
    
    def is_user(self):
        """Verifica si el usuario es User/Client"""
        return self.role == self.ROLE_USER
    
    def can_manage_users(self):
        """Verifica si puede acceder a gestión de usuarios"""
        return self.is_super_admin() or self.is_admin()
    
    @property
    def display_name(self):
        """Nombre para mostrar en UI"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.full_name or self.email.split('@')[0]
    
    def get_or_create_preferences(self):
        """Obtiene o crea preferencias del usuario"""
        from accounts.models import UserPreferences
        prefs, created = UserPreferences.objects.get_or_create(user=self)
        return prefs
    
    def get_or_create_security(self):
        """Obtiene o crea configuración de seguridad"""
        from accounts.models import SecuritySettings
        security, created = SecuritySettings.objects.get_or_create(user=self)
        return security
    
    # ============================================================================
    # MÉTODOS PARA VALIDACIÓN DE PERFIL OPERATIVO
    # ============================================================================
    
    def check_profile_completed(self):
        """
        Verifica si el perfil operativo está completo.
        
        Retorna True si todos los campos obligatorios están completados:
        - telefono_reparto
        - direccion_local, ciudad, provincia, codigo_postal
        - tipo_entrega
        - direccion_entrega, ciudad_entrega, provincia_entrega, codigo_postal_entrega
        """
        required_fields = [
            self.telefono_reparto,
            self.direccion_local,
            self.ciudad,
            self.provincia,
            self.codigo_postal,
            self.tipo_entrega,
            self.direccion_entrega,
            self.ciudad_entrega,
            self.provincia_entrega,
            self.codigo_postal_entrega,
        ]
        # Todos los campos deben tener contenido (no vacíos ni None)
        return all(field and str(field).strip() for field in required_fields)
    
    @property
    def missing_fields(self):
        """
        Retorna lista de nombres de campos obligatorios que faltan por completar.
        
        Se usa para mostrar feedback al usuario sobre qué campos necesita completar.
        """
        missing = []

        if not self.telefono_reparto or not str(self.telefono_reparto).strip():
            missing.append(_("Teléfono de reparto"))

        if not self.direccion_local or not str(self.direccion_local).strip():
            missing.append(_("Dirección local"))

        if not self.ciudad or not str(self.ciudad).strip():
            missing.append(_("Ciudad"))

        if not self.provincia or not str(self.provincia).strip():
            missing.append(_("Provincia"))

        if not self.codigo_postal or not str(self.codigo_postal).strip():
            missing.append(_("Código postal"))

        if not self.tipo_entrega or not str(self.tipo_entrega).strip():
            missing.append(_("Tipo de entrega"))

        if not self.direccion_entrega or not str(self.direccion_entrega).strip():
            missing.append(_("Dirección de entrega"))

        if not self.ciudad_entrega or not str(self.ciudad_entrega).strip():
            missing.append(_("Ciudad de entrega"))

        if not self.provincia_entrega or not str(self.provincia_entrega).strip():
            missing.append(_("Provincia de entrega"))

        if not self.codigo_postal_entrega or not str(self.codigo_postal_entrega).strip():
            missing.append(_("Código postal de entrega"))

        return missing
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe save para actualizar automáticamente profile_completed
        cada vez que se guarda el usuario.
        """
        # Actualizar el flag de completitud antes de guardar
        self.profile_completed = self.check_profile_completed()
        super().save(*args, **kwargs)


class EmailVerificationToken(models.Model):
    """Token para verificación de email"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verification_tokens'
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('Token de Verificación')
        verbose_name_plural = _('Tokens de Verificación')
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Verifica si el token es válido"""
        return not self.is_used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f'Token for {self.user.email}'


# ============================================================================
# MODELOS EXTENDIDOS PARA PERFIL PROFESIONAL
# ============================================================================

class UserPreferences(models.Model):
    """Preferencias de usuario"""
    
    THEME_CHOICES = [
        ('light', _('Claro')),
        ('dark', _('Oscuro')),
        ('system', _('Sistema')),
    ]
    
    DETAIL_LEVEL_CHOICES = [
        ('low', _('Bajo')),
        ('medium', _('Medio')),
        ('high', _('Alto')),
    ]
    
    FORMAT_CHOICES = [
        ('structured', _('Estructurado')),
        ('narrative', _('Narrativo')),
        ('bullet_points', _('Puntos clave')),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    # UI/UX
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='system')
    language = models.CharField(max_length=10, default='es')
    timezone = models.CharField(max_length=50, default='Europe/Madrid')
    
    # NOTIFICACIONES
    email_notifications = models.BooleanField(default=True)
    platform_notifications = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)
    
    # IA PREFERENCES
    ai_language = models.CharField(max_length=10, default='es', verbose_name=_('Idioma IA'))
    ai_detail_level = models.CharField(max_length=20, choices=DETAIL_LEVEL_CHOICES, default='medium')
    ai_format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='structured')
    
    # FECHAS
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Preferencias de Usuario')
        verbose_name_plural = _('Preferencias de Usuarios')
    
    def __str__(self):
        return f"Preferencias de {self.user.email}"


class SecuritySettings(models.Model):
    """Configuración de seguridad del usuario"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='security')
    
    # 2FA
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_method = models.CharField(max_length=20, blank=True)  # 'totp', 'sms', 'email'
    two_factor_secret = models.CharField(max_length=100, blank=True)
    
    # API
    api_token = models.CharField(max_length=100, blank=True, null=True, unique=True, default=None)
    api_token_created_at = models.DateTimeField(null=True, blank=True)
    api_token_last_used = models.DateTimeField(null=True, blank=True)
    
    # SESIONES
    max_concurrent_sessions = models.IntegerField(default=3)
    session_timeout_minutes = models.IntegerField(default=60)
    
    # FECHAS
    password_changed_at = models.DateTimeField(null=True, blank=True)
    password_expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Configuración de Seguridad')
        verbose_name_plural = _('Configuraciones de Seguridad')
    
    def __str__(self):
        return f"Seguridad de {self.user.email}"


class UserSession(models.Model):
    """Registro de sesiones activas"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=100, unique=True)
    
    # METADATA
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=50, blank=True)  # 'desktop', 'mobile', 'tablet'
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    
    # ESTADO
    is_active = models.BooleanField(default=True)
    
    # FECHAS
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        verbose_name = _('Sesión de Usuario')
        verbose_name_plural = _('Sesiones de Usuarios')
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.ip_address}"


class LoginHistory(models.Model):
    """Historial de inicios de sesión"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    
    # EVENTO
    success = models.BooleanField(default=True)
    failure_reason = models.CharField(max_length=200, blank=True)
    
    # METADATA
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)  # Ciudad/País estimado
    
    # FECHA
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Historial de Login')
        verbose_name_plural = _('Historiales de Login')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['success']),
        ]
    
    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.user.email} - {self.created_at}"


class ProfileAuditLog(models.Model):
    """Log de auditoría de cambios en perfil"""
    
    ACTION_CHOICES = [
        ('update_personal', _('Actualización datos personales')),
        ('update_company', _('Actualización datos empresa')),
        ('update_preferences', _('Actualización preferencias')),
        ('update_security', _('Actualización seguridad')),
        ('change_password', _('Cambio de contraseña')),
        ('enable_2fa', _('Activación 2FA')),
        ('disable_2fa', _('Desactivación 2FA')),
        ('avatar_upload', _('Subida de avatar')),
        ('avatar_delete', _('Eliminación de avatar')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    
    # CAMBIOS
    field_changed = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    
    # METADATA
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # FECHA
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Log de Auditoría')
        verbose_name_plural = _('Logs de Auditoría')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_action_display()} - {self.created_at}"

