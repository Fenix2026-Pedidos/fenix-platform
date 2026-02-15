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
    
    # Campos readonly que no se pueden editar desde el formulario
    email = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'style': 'background-color: #f8f9fa; cursor: not-allowed;'
        }),
        label=_('Email')
    )
    
    company = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'style': 'background-color: #f8f9fa; cursor: not-allowed;',
            'placeholder': _('Configurable por administrador')
        }),
        label=_('Empresa')
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-popular campos readonly con valores actuales
        if self.instance and self.instance.pk:
            self.fields['email'].initial = self.instance.email
            self.fields['company'].initial = self.instance.company or '-'
    
    def save(self, commit=True):
        # No permitir que se actualicen email ni company desde este formulario
        if 'email' in self.changed_data:
            self.changed_data.remove('email')
        if 'company' in self.changed_data:
            self.changed_data.remove('company')
        return super().save(commit=commit)


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


# ============================================================================
# FORMULARIO PARA PERFIL OPERATIVO (NUEVO)
# ============================================================================

class OperativeProfileForm(forms.ModelForm):
    """
    Formulario para editar el perfil operativo del usuario.
    
    Todos los campos marcados aquí como required=True son OBLIGATORIOS
    para poder crear pedidos.
    
    Los campos se organizan en 4 secciones visuales:
    1. Contacto
    2. Dirección fiscal/local
    3. Dirección de entrega
    """
    
    class Meta:
        model = User
        fields = [
            # Contacto
            'telefono_empresa',
            'telefono_reparto',
            # Dirección fiscal/local
            'direccion_local',
            'ciudad',
            'provincia',
            'codigo_postal',
            'pais',
            # Dirección de entrega
            'tipo_entrega',
            'direccion_entrega',
            'ciudad_entrega',
            'provincia_entrega',
            'codigo_postal_entrega',
            'ventana_entrega',
            'observaciones_entrega',
        ]
        widgets = {
            # ========== CONTACTO ==========
            'telefono_empresa': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '+34 XXX XXX XXX',
                'type': 'tel'
            }),
            'telefono_reparto': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '+34 XXX XXX XXX (OBLIGATORIO)',
                'type': 'tel',
                'aria-required': 'true',
            }),
            
            # ========== DIRECCIÓN FISCAL/LOCAL ==========
            'direccion_local': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Calle, número y piso (OBLIGATORIO)',
            }),
            'ciudad': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ciudad (OBLIGATORIO)',
            }),
            'provincia': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Provincia (OBLIGATORIO)',
            }),
            'codigo_postal': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '28001 (OBLIGATORIO)',
                'maxlength': '10',
            }),
            'pais': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'España',
            }),
            
            # ========== DIRECCIÓN DE ENTREGA ==========
            'tipo_entrega': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white',
            }),
            'direccion_entrega': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Calle, número y piso (OBLIGATORIO)',
            }),
            'ciudad_entrega': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ciudad (OBLIGATORIO)',
            }),
            'provincia_entrega': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Provincia (OBLIGATORIO)',
            }),
            'codigo_postal_entrega': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '28001 (OBLIGATORIO)',
                'maxlength': '10',
            }),
            'ventana_entrega': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ej: Lunes 9:00-13:00 (opcional)',
            }),
            'observaciones_entrega': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Instrucciones especiales para la entrega (opcional)',
                'rows': 3,
            }),
        }
        labels = {
            # Contacto
            'telefono_empresa': _('Teléfono de empresa'),
            'telefono_reparto': _('Teléfono de reparto *'),
            # Dirección fiscal/local
            'direccion_local': _('Dirección local *'),
            'ciudad': _('Ciudad *'),
            'provincia': _('Provincia *'),
            'codigo_postal': _('Código postal *'),
            'pais': _('País'),
            # Dirección de entrega
            'tipo_entrega': _('Tipo de entrega *'),
            'direccion_entrega': _('Dirección de entrega *'),
            'ciudad_entrega': _('Ciudad de entrega *'),
            'provincia_entrega': _('Provincia de entrega *'),
            'codigo_postal_entrega': _('Código postal de entrega *'),
            'ventana_entrega': _('Ventana de entrega'),
            'observaciones_entrega': _('Observaciones'),
        }
        help_texts = {
            'telefono_reparto': _('Teléfono de contacto para confirmar la entrega'),
            'tipo_entrega': _('Selecciona si prefieres recoger en el local o que se envíe a domicilio'),
            'ventana_entrega': _('Ej: Lunes a viernes 9:00-14:00'),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Marcar campos obligatorios
        obligatorios = [
            'telefono_reparto',
            'direccion_local',
            'ciudad',
            'provincia',
            'codigo_postal',
            'tipo_entrega',
            'direccion_entrega',
            'ciudad_entrega',
            'provincia_entrega',
            'codigo_postal_entrega',
        ]
        
        for field_name in obligatorios:
            self.fields[field_name].required = True
            # Añadir clase CSS de error si el campo tiene errores
            if field_name in self.errors:
                current_class = self.fields[field_name].widget.attrs.get('class', '')
                self.fields[field_name].widget.attrs['class'] = current_class + ' border-red-500'
    
    def clean(self):
        """Validación adicional a nivel de formulario"""
        cleaned_data = super().clean()
        
        # Si tipo_entrega es "envio", ambas direcciones deben ser diferentes
        tipo_entrega = cleaned_data.get('tipo_entrega')
        if tipo_entrega == User.TIPO_ENTREGA_ENVIO:
            dir_local = cleaned_data.get('direccion_local')
            dir_entrega = cleaned_data.get('direccion_entrega')
            
            # Podrían ser iguales (ej: llevar a la misma dirección), así que no validamos
        
        return cleaned_data
