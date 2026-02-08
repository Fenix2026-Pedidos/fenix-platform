from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from simple_history.models import HistoricalRecords
import uuid


class Company(models.Model):
    """Modelo de empresa para multitenancy"""
    
    SECTOR_CHOICES = [
        ('tech', _('Tecnología')),
        ('finance', _('Finanzas')),
        ('retail', _('Retail')),
        ('manufacturing', _('Manufactura')),
        ('services', _('Servicios')),
        ('healthcare', _('Salud')),
        ('education', _('Educación')),
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
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    
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
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


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
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['company', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.email} @ {self.company.name}"


# MANTENER COMPATIBILIDAD CON CÓDIGO EXISTENTE
class Organization(models.Model):
    """Modelo legacy - mantener por compatibilidad"""
    LANGUAGE_ES = 'es'
    LANGUAGE_ZH_HANS = 'zh-hans'

    LANGUAGE_CHOICES = [
        (LANGUAGE_ES, 'Español'),
        (LANGUAGE_ZH_HANS, 'Chinese (Simplified)'),
    ]

    name = models.CharField(max_length=200)
    default_language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default=LANGUAGE_ES,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'

    def __str__(self) -> str:
        return self.name
