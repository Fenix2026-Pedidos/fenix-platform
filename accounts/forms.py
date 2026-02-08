from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import User


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Email'),
            'autofocus': True
        })
    )
    password = forms.CharField(
        label=_('Contraseña'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Contraseña')
        })
    )


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label=_('Contraseña'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Contraseña'),
            'id': 'id_password1'
        })
    )
    password2 = forms.CharField(
        label=_('Confirmar contraseña'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Confirmar contraseña'),
            'id': 'id_password2'
        })
    )

    class Meta:
        model = User
        fields = ('full_name', 'email', 'company')
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Tu nombre completo')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('tu@email.com')
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nombre de tu empresa')
            }),
        }
        labels = {
            'full_name': _('Nombre completo'),
            'email': _('Correo electrónico'),
            'company': _('Empresa'),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_('Las contraseñas no coinciden.'))
        return password2
    
    def clean_company(self):
        company = self.cleaned_data.get('company')
        if not company:
            raise forms.ValidationError(_('La empresa es obligatoria.'))
        return company

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.language = User.LANGUAGE_ES  # Default español
        if commit:
            user.save()
        return user
