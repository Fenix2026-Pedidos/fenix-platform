from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    """Formulario para crear/editar productos (Manager/Super Admin)"""
    
    class Meta:
        model = Product
        fields = [
            'name_es',
            'name_zh_hans',
            'description_es',
            'description_zh_hans',
            'image',
            'price',
            'stock_available',
            'stock_min_threshold',
            'is_active',
        ]
        widgets = {
            'name_es': forms.TextInput(attrs={'class': 'form-control'}),
            'name_zh_hans': forms.TextInput(attrs={'class': 'form-control'}),
            'description_es': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'description_zh_hans': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_available': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_min_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name_es': 'Nombre (Español)',
            'name_zh_hans': 'Nombre (中文)',
            'description_es': 'Descripción (Español)',
            'description_zh_hans': 'Descripción (中文)',
            'image': 'Imagen',
            'price': 'Precio',
            'stock_available': 'Stock Disponible',
            'stock_min_threshold': 'Stock Mínimo',
            'is_active': 'Activo',
        }


class StockUpdateForm(forms.Form):
    """Formulario para ajustar stock rápidamente"""
    adjustment = forms.IntegerField(
        label='Ajuste de Stock',
        help_text='Cantidad a sumar (+) o restar (-)',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        label='Notas',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
