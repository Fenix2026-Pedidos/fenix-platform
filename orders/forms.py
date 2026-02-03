from django import forms
from .models import Order, OrderEvent, OrderDocument
from django.utils.translation import gettext_lazy as _


class OrderStatusUpdateForm(forms.Form):
    """Formulario para cambiar el estado de un pedido"""
    status = forms.ChoiceField(
        choices=Order.STATUS_CHOICES,
        label=_('Nuevo Estado'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    note = forms.CharField(
        label=_('Nota'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Añade comentarios sobre este cambio de estado...')
        })
    )


class OrderETAForm(forms.ModelForm):
    """Formulario para asignar ETA (fechas estimadas de entrega)"""
    
    class Meta:
        model = Order
        fields = ['eta_start', 'eta_end']
        widgets = {
            'eta_start': forms.DateTimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'datetime-local'
                }
            ),
            'eta_end': forms.DateTimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'datetime-local'
                }
            ),
        }
        labels = {
            'eta_start': _('Fecha estimada (inicio)'),
            'eta_end': _('Fecha estimada (fin)'),
        }

    def clean(self):
        cleaned_data = super().clean()
        eta_start = cleaned_data.get('eta_start')
        eta_end = cleaned_data.get('eta_end')

        if eta_start and eta_end and eta_start >= eta_end:
            raise forms.ValidationError(_('La fecha de inicio debe ser anterior a la fecha de fin.'))

        return cleaned_data


class OrderDocumentForm(forms.ModelForm):
    """Formulario para subir documentos a un pedido"""
    
    class Meta:
        model = OrderDocument
        fields = ['document_type', 'title', 'description', 'file']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'document_type': _('Tipo de documento'),
            'title': _('Título'),
            'description': _('Descripción'),
            'file': _('Archivo'),
        }

