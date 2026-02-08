# 🏗️ Módulo de Perfil de Usuario - Arquitectura Enterprise SaaS

## 📐 1. WIREFRAME TEXTUAL DEL LAYOUT

```
┌─────────────────────────────────────────────────────────────┐
│  MI PERFIL                                  [vladimir@...]   │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────┬──────────────────────────────────┐
│  📋 DATOS PERSONALES     │  🏢 EMPRESA / ORGANIZACIÓN       │
│  [Editar]                │  [Editar]                        │
│                          │                                  │
│  👤 Avatar               │  Empresa: Fenix Ltd              │
│  Nombre: Vladimir        │  CIF/VAT: ES-B12345678           │
│  Apellidos: Marfetan     │  Sector: Tecnología              │
│  Email: v...@gmail.com   │  País: España                    │
│  Teléfono: +34 600...    │  Ciudad: Madrid                  │
│  Idioma: Español         │  Cargo: CTO                      │
│  Estado: 🟢 Activo       │  Departamento: Engineering       │
│  Registrado: 25/01/2026  │  Rol: Super Admin                │
│  Último acceso: Hoy      │                                  │
│  ID: #1234               │                                  │
│  UUID: a1b2c3d4...       │                                  │
└──────────────────────────┴──────────────────────────────────┘

┌──────────────────────────┬──────────────────────────────────┐
│  🔐 SEGURIDAD Y CUENTA   │  ⚙️ PREFERENCIAS                 │
│  [Gestionar]             │  [Editar]                        │
│                          │                                  │
│  🔑 Cambiar contraseña   │  Idioma: Español                 │
│  🛡️ 2FA: Desactivado     │  Tema: Oscuro                    │
│     [Activar]            │  Notificaciones:                 │
│  📱 Sesiones activas: 2  │    ✅ Email                      │
│     [Ver todas]          │    ✅ Plataforma                 │
│  🚪 Último login:        │  🤖 IA Preferencias:             │
│     04/02/2026 09:30     │    Idioma: Español               │
│  🌐 IP: 192.168.1.100    │    Detalle: Alto                 │
│  📊 [Ver historial]      │    Formato: Estructurado         │
└──────────────────────────┴──────────────────────────────────┘
```

---

## 🗄️ 2. ESQUEMA DE BASE DE DATOS

### Modelos Django Extendidos

```python
# accounts/models.py (EXTENDIDO)

from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid
from simple_history.models import HistoricalRecords  # Para auditoría


class User(AbstractBaseUser, PermissionsMixin):
    """Usuario extendido con campos profesionales"""
    
    # ROLES
    ROLE_SUPER_ADMIN = 'super_admin'
    ROLE_ADMIN = 'admin'
    ROLE_USER = 'user'
    
    ROLE_CHOICES = [
        (ROLE_SUPER_ADMIN, _('Super Admin')),
        (ROLE_ADMIN, _('Admin')),
        (ROLE_USER, _('User')),
    ]
    
    # ESTADOS
    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_DISABLED = 'disabled'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pendiente')),
        (STATUS_ACTIVE, _('Activo')),
        (STATUS_INACTIVE, _('Inactivo')),
        (STATUS_DISABLED, _('Deshabilitado')),
    ]
    
    # IDENTIFICACIÓN
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(unique=True)
    
    # DATOS PERSONALES
    first_name = models.CharField(max_length=100, blank=True, verbose_name=_('Nombre'))
    last_name = models.CharField(max_length=100, blank=True, verbose_name=_('Apellidos'))
    full_name = models.CharField(max_length=200)  # Mantener por compatibilidad
    phone = models.CharField(max_length=20, blank=True, verbose_name=_('Teléfono'))
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # SISTEMA
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_USER)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    language = models.CharField(max_length=10, default='es')
    timezone = models.CharField(max_length=50, default='Europe/Madrid')
    
    # FLAGS
    email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # FECHAS
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # RELACIONES
    company = models.ForeignKey('organizations.Company', on_delete=models.SET_NULL, 
                                null=True, blank=True, related_name='users')
    
    # AUDITORÍA
    history = HistoricalRecords()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    class Meta:
        verbose_name = _('Usuario')
        verbose_name_plural = _('Usuarios')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['uuid']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return self.email
    
    @property
    def display_name(self):
        """Nombre para mostrar en UI"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.full_name or self.email


# organizations/models.py (NUEVO)

class Company(models.Model):
    """Modelo de empresa para multitenancy"""
    
    SECTOR_CHOICES = [
        ('tech', _('Tecnología')),
        ('finance', _('Finanzas')),
        ('retail', _('Retail')),
        ('manufacturing', _('Manufactura')),
        ('services', _('Servicios')),
        ('other', _('Otro')),
    ]
    
    SIZE_CHOICES = [
        ('1-10', '1-10 empleados'),
        ('11-50', '11-50 empleados'),
        ('51-200', '51-200 empleados'),
        ('201-500', '201-500 empleados'),
        ('500+', '500+ empleados'),
    ]
    
    # IDENTIFICACIÓN
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=200, verbose_name=_('Nombre'))
    slug = models.SlugField(max_length=200, unique=True)
    
    # DATOS FISCALES
    vat_number = models.CharField(max_length=50, blank=True, verbose_name=_('CIF/VAT'))
    tax_id = models.CharField(max_length=50, blank=True, verbose_name=_('Tax ID'))
    
    # CLASIFICACIÓN
    sector = models.CharField(max_length=50, choices=SECTOR_CHOICES, blank=True)
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, blank=True)
    
    # UBICACIÓN
    country = models.CharField(max_length=100, blank=True, verbose_name=_('País'))
    city = models.CharField(max_length=100, blank=True, verbose_name=_('Ciudad'))
    address = models.TextField(blank=True, verbose_name=_('Dirección'))
    postal_code = models.CharField(max_length=20, blank=True)
    
    # CONTACTO
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    
    # CONFIGURACIÓN
    logo = models.ImageField(upload_to='companies/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # FECHAS
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # AUDITORÍA
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Empresa')
        verbose_name_plural = _('Empresas')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserCompany(models.Model):
    """Relación User-Company con rol y cargo"""
    
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='company_memberships')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='memberships')
    
    # ROL EN LA EMPRESA
    job_title = models.CharField(max_length=100, blank=True, verbose_name=_('Cargo'))
    department = models.CharField(max_length=100, blank=True, verbose_name=_('Departamento'))
    
    # PERMISOS
    is_company_admin = models.BooleanField(default=False)
    is_billing_contact = models.BooleanField(default=False)
    
    # FECHAS
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Usuario-Empresa')
        verbose_name_plural = _('Usuarios-Empresas')
        unique_together = [['user', 'company']]
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.email} @ {self.company.name}"


# accounts/models.py (NUEVO)

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
    
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='preferences')
    
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
    
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='security')
    
    # 2FA
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_method = models.CharField(max_length=20, blank=True)  # 'totp', 'sms', 'email'
    two_factor_secret = models.CharField(max_length=100, blank=True)
    
    # API
    api_token = models.CharField(max_length=100, blank=True, unique=True)
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
    
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='sessions')
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
    
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='login_history')
    
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
    ]
    
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='audit_logs')
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
```

---

## 🛣️ 3. API ENDPOINTS (Django Views)

```python
# accounts/urls.py

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # PERFIL COMPLETO
    path('profile/', views.profile_view, name='profile'),
    
    # ACTUALIZACIÓN POR SECCIONES
    path('profile/personal/', views.update_personal_data, name='update_personal'),
    path('profile/company/', views.update_company_data, name='update_company'),
    path('profile/preferences/', views.update_preferences, name='update_preferences'),
    path('profile/security/', views.update_security, name='update_security'),
    
    # SEGURIDAD
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/enable-2fa/', views.enable_2fa, name='enable_2fa'),
    path('profile/disable-2fa/', views.disable_2fa, name='disable_2fa'),
    
    # SESIONES
    path('profile/sessions/', views.active_sessions, name='active_sessions'),
    path('profile/sessions/<int:session_id>/revoke/', views.revoke_session, name='revoke_session'),
    path('profile/sessions/revoke-all/', views.revoke_all_sessions, name='revoke_all'),
    
    # AVATAR
    path('profile/avatar/', views.upload_avatar, name='upload_avatar'),
    path('profile/avatar/delete/', views.delete_avatar, name='delete_avatar'),
    
    # HISTORIAL
    path('profile/login-history/', views.login_history, name='login_history'),
    path('profile/audit-log/', views.audit_log, name='audit_log'),
    
    # API TOKEN
    path('profile/api-token/generate/', views.generate_api_token, name='generate_api_token'),
    path('profile/api-token/revoke/', views.revoke_api_token, name='revoke_api_token'),
]
```

---

## 🎨 4. FRONTEND - ESTRUCTURA DE TEMPLATES

```
templates/accounts/
├── profile/
│   ├── profile_dashboard.html       # Página principal con 4 cards
│   ├── _personal_card.html          # Card de datos personales
│   ├── _company_card.html           # Card de empresa
│   ├── _security_card.html          # Card de seguridad
│   ├── _preferences_card.html       # Card de preferencias
│   ├── edit_personal.html           # Modal/form datos personales
│   ├── edit_company.html            # Modal/form empresa
│   ├── edit_preferences.html        # Modal/form preferencias
│   ├── change_password.html         # Modal cambio contraseña
│   ├── sessions_list.html           # Lista de sesiones activas
│   ├── login_history.html           # Historial de logins
│   └── audit_log.html               # Log de auditoría
└── components/
    ├── avatar_upload.html           # Componente de avatar
    ├── editable_card.html           # Card base editable
    └── status_badge.html            # Badge de estado
```

---

## 📋 5. IMPLEMENTACIÓN PASO A PASO

### Paso 1: Crear nuevas apps y modelos
### Paso 2: Migrar datos existentes
### Paso 3: Crear vistas y templates
### Paso 4: Añadir JavaScript para interactividad
### Paso 5: Tests y auditoría

---

## ✨ PRÓXIMOS PASOS

¿Quieres que implemente:
1. **Los modelos Django completos** con migraciones
2. **Las vistas y formularios** para cada sección
3. **Los templates HTML** con Tailwind/Bootstrap
4. **El JavaScript** para edición inline
5. **Todo lo anterior** (implementación completa)

Dime qué prefieres y empiezo a codificar 🚀
