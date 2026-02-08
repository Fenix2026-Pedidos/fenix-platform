from django import forms
from django.contrib.auth.forms import PasswordChangeForm as BasePasswordChangeForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import User, UserPreferences, SecuritySettings
from organizations.models import UserCompany

# Timezones comunes
TIMEZONE_CHOICES = [
    ('Europe/Madrid', 'España (Madrid)'),
    ('Europe/London', 'Reino Unido (Londres)'),
    ('Europe/Paris', 'Francia (París)'),
    ('Europe/Berlin', 'Alemania (Berlín)'),
    ('Europe/Rome', 'Italia (Roma)'),
    ('Europe/Lisbon', 'Portugal (Lisboa)'),
    ('America/New_York', 'EE.UU. (Nueva York)'),
    ('America/Chicago', 'EE.UU. (Chicago)'),
    ('America/Denver', 'EE.UU. (Denver)'),
    ('America/Los_Angeles', 'EE.UU. (Los Ángeles)'),
    ('America/Mexico_City', 'México (Ciudad de México)'),
    ('America/Bogota', 'Colombia (Bogotá)'),
    ('America/Lima', 'Perú (Lima)'),
    ('America/Santiago', 'Chile (Santiago)'),
    ('America/Buenos_Aires', 'Argentina (Buenos Aires)'),
    ('America/Sao_Paulo', 'Brasil (São Paulo)'),
    ('Asia/Tokyo', 'Japón (Tokio)'),
    ('Asia/Shanghai', 'China (Shanghai)'),
    ('Asia/Dubai', 'Emiratos (Dubái)'),
    ('Australia/Sydney', 'Australia (Sídney)'),
    ('UTC', 'UTC'),
]


class PersonalDataForm(forms.ModelForm):
    """Formulario para editar datos personales del usuario"""
    
    timezone = forms.ChoiceField(
        choices=TIMEZONE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('Zona Horaria'),
        required=False
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'timezone']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nombre')
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Apellido')
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+34 XXX XXX XXX'
            }),
        }
        labels = {
            'first_name': _('Nombre'),
            'last_name': _('Apellido'),
            'phone': _('Teléfono'),
            'timezone': _('Zona Horaria'),
        }


class CompanyDataForm(forms.ModelForm):
    """Formulario para editar datos de la empresa del usuario"""
    
    class Meta:
        model = UserCompany
        fields = ['job_title', 'department']
        widgets = {
            'job_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ej: Gerente de Ventas')
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ej: Ventas')
            }),
        }
        labels = {
            'job_title': _('Cargo'),
            'department': _('Departamento'),
        }


class PreferencesForm(forms.ModelForm):
    """Formulario para editar preferencias del usuario"""
    
    class Meta:
        model = UserPreferences
        fields = [
            'theme', 'language', 'timezone',
            'email_notifications', 'platform_notifications', 'marketing_emails',
            'ai_language', 'ai_detail_level', 'ai_format'
        ]
        widgets = {
            'theme': forms.Select(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
            'timezone': forms.Select(attrs={'class': 'form-control'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'platform_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'marketing_emails': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ai_language': forms.Select(attrs={'class': 'form-control'}),
            'ai_detail_level': forms.Select(attrs={'class': 'form-control'}),
            'ai_format': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'theme': _('Tema'),
            'language': _('Idioma'),
            'timezone': _('Zona Horaria'),
            'email_notifications': _('Notificaciones por Email'),
            'platform_notifications': _('Notificaciones en la Plataforma'),
            'marketing_emails': _('Emails de Marketing'),
            'ai_language': _('Idioma IA'),
            'ai_detail_level': _('Nivel de Detalle IA'),
            'ai_format': _('Formato de Respuesta IA'),
        }


class SecurityForm(forms.ModelForm):
    """Formulario para configurar ajustes de seguridad"""
    
    class Meta:
        model = SecuritySettings
        fields = [
            'two_factor_enabled', 'two_factor_method',
            'max_concurrent_sessions', 'session_timeout_minutes'
        ]
        widgets = {
            'two_factor_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'two_factor_method': forms.Select(attrs={'class': 'form-control'}),
            'max_concurrent_sessions': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10
            }),
            'session_timeout_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 5,
                'max': 1440
            }),
        }
        labels = {
            'two_factor_enabled': _('Habilitar Autenticación de Dos Factores'),
            'two_factor_method': _('Método de 2FA'),
            'max_concurrent_sessions': _('Máximo de Sesiones Simultáneas'),
            'session_timeout_minutes': _('Tiempo de Espera de Sesión (minutos)'),
        }


class PasswordChangeForm(BasePasswordChangeForm):
    """Formulario para cambiar contraseña"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Contraseña actual')
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Nueva contraseña')
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Confirmar nueva contraseña')
        })


class AvatarUploadForm(forms.ModelForm):
    """Formulario para subir avatar"""
    
    class Meta:
        model = User
        fields = ['avatar']
        widgets = {
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # Validar tamaño (máximo 5MB)
            if avatar.size > 5 * 1024 * 1024:
                raise ValidationError(_('El archivo es demasiado grande. Tamaño máximo: 5MB'))
            
            # Validar tipo de archivo
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if avatar.content_type not in allowed_types:
                raise ValidationError(_('Tipo de archivo no permitido. Use JPG, PNG, GIF o WebP'))
        
        return avatar
