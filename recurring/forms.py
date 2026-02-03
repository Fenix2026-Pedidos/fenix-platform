from django import forms
from .models import RecurringOrder, RecurringOrderItem
from catalog.models import Product
from django.utils.translation import gettext_lazy as _


class RecurringOrderForm(forms.ModelForm):
    """Formulario para crear/editar pedidos recurrentes"""
    
    class Meta:
        model = RecurringOrder
        fields = ['frequency', 'start_date', 'end_date', 'delivery_window_hours']
        widgets = {
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'delivery_window_hours': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'frequency': _('Frecuencia'),
            'start_date': _('Fecha de inicio'),
            'end_date': _('Fecha de fin (opcional)'),
            'delivery_window_hours': _('Ventana de entrega (horas)'),
        }
        help_texts = {
            'end_date': _('Dejar vacío para pedidos recurrentes indefinidos'),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError(_('La fecha de fin debe ser posterior a la fecha de inicio.'))

        return cleaned_data
