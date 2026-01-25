from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
import logging
from .models import Product
from .utils import translate_product_fields

logger = logging.getLogger(__name__)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name_es', 'name_zh_hans', 'price', 'stock_available',
        'stock_min_threshold', 'stock_status', 'is_active', 'created_at',
    )
    list_filter = ('stock_status', 'is_active')
    search_fields = ('name_es', 'name_zh_hans')
    readonly_fields = ('stock_status', 'created_at', 'image_preview', 'translate_button')
    fieldsets = (
        (None, {'fields': ('name_es', 'name_zh_hans', 'description_es', 'description_zh_hans', 'translate_button', 'image', 'image_preview', 'price', 'is_active')}),
        ('Stock (solo managers)', {'fields': ('stock_available', 'stock_min_threshold', 'stock_status')}),
        ('Auditoría', {'fields': ('created_at',)}),
    )
    
    def image_preview(self, obj):
        """Muestra una vista previa de la imagen en el admin"""
        if obj is None:
            return mark_safe('<span style="color: var(--gray-500);">Sin imagen</span>')
        
        if not hasattr(obj, 'pk') or not obj.pk:
            return mark_safe('<span style="color: var(--gray-500);">Sin imagen</span>')
        
        if not hasattr(obj, 'image') or not obj.image:
            return mark_safe('<span style="color: var(--gray-500);">Sin imagen</span>')
        
        try:
            image_url = obj.image.url
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 8px;" />',
                image_url
            )
        except (AttributeError, ValueError, Exception):
            return mark_safe('<span style="color: var(--gray-500);">Sin imagen</span>')
    image_preview.short_description = 'Vista previa'
    
    def translate_button(self, obj):
        """Botón para traducir automáticamente de español a chino"""
        if obj is None:
            return mark_safe(
                '<p style="color: var(--gray-500); font-size: 12px;">'
                'Guarda el producto primero para habilitar la traducción automática.'
                '</p>'
            )
        
        if not hasattr(obj, 'pk') or not obj.pk:
            return mark_safe(
                '<p style="color: var(--gray-500); font-size: 12px;">'
                'Guarda el producto primero para habilitar la traducción automática.'
                '</p>'
            )
        
        # Solo mostrar si el objeto ya existe
        return mark_safe(
            '<button type="button" onclick="translateProduct()" class="button" style="'
            'background: var(--primary-600); color: white; border: none; padding: 8px 16px; '
            'border-radius: 4px; cursor: pointer; font-size: 13px;'
            '">'
            '🌐 Traducir automáticamente (ES → 中文)'
            '</button>'
            '<script>'
            'function translateProduct() {'
            '  if (confirm("¿Traducir automáticamente el nombre y descripción de español a chino simplificado?")) {'
            '    var nameEs = document.getElementById("id_name_es").value;'
            '    var descEs = document.getElementById("id_description_es").value;'
            '    if (!nameEs && !descEs) {'
            '      alert("Por favor, completa primero los campos en español.");'
            '      return;'
            '    }'
            '    var currentPath = window.location.pathname;'
            '    var translateUrl = currentPath.endsWith("/") ? currentPath + "translate/" : currentPath + "/translate/";'
            '    fetch(translateUrl, {'
            '      method: "POST",'
            '      headers: {'
            '        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,'
            '        "Content-Type": "application/x-www-form-urlencoded",'
            '      },'
            '      body: "name_es=" + encodeURIComponent(nameEs) + "&description_es=" + encodeURIComponent(descEs)'
            '    })'
            '    .then(response => response.json())'
            '    .then(data => {'
            '      if (data.success) {'
            '        if (data.name_zh_hans) document.getElementById("id_name_zh_hans").value = data.name_zh_hans;'
            '        if (data.description_zh_hans) document.getElementById("id_description_zh_hans").value = data.description_zh_hans;'
            '        alert("Traducción completada. Revisa los campos y guarda el producto.");'
            '      } else {'
            '        alert("Error: " + (data.error || "No se pudo traducir"));'
            '      }'
            '    })'
            '    .catch(error => {'
            '      alert("Error al traducir: " + error);'
            '    });'
            '  }'
            '}'
            '</script>'
        )
    translate_button.short_description = 'Traducción Automática'
    translate_button.allow_tags = True
    
    def get_urls(self):
        """Añade URL personalizada para la traducción"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:object_id>/translate/',
                self.admin_site.admin_view(self.translate_view),
                name='catalog_product_translate',
            ),
        ]
        return custom_urls + urls
    
    def translate_view(self, request, object_id):
        """Vista para traducir un producto"""
        from django.http import JsonResponse
        
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
        
        try:
            product = Product.objects.get(pk=object_id)
            
            # Obtener valores actuales del formulario (pueden haber sido modificados)
            name_es = request.POST.get('name_es') or product.name_es
            description_es = request.POST.get('description_es') or product.description_es
            
            # Crear un objeto temporal para traducir
            temp_product = Product(name_es=name_es, description_es=description_es)
            
            # Traducir campos
            translated = translate_product_fields(temp_product)
            
            if translated:
                return JsonResponse({
                    'success': True,
                    'name_zh_hans': translated.get('name_zh_hans', ''),
                    'description_zh_hans': translated.get('description_zh_hans', ''),
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'No hay campos en español para traducir'
                })
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Producto no encontrado'
            })
        except Exception as e:
            import traceback
            logger.error(f"Error en traducción: {traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    def save_model(self, request, obj, form, change):
        """Al guardar, si solo hay campos en español, traducir automáticamente"""
        # Si es un nuevo producto y tiene name_es pero no name_zh_hans, traducir automáticamente
        if not change and obj.name_es and not obj.name_zh_hans:
            try:
                translated = translate_product_fields(obj)
                if translated.get('name_zh_hans'):
                    obj.name_zh_hans = translated['name_zh_hans']
                if translated.get('description_zh_hans'):
                    obj.description_zh_hans = translated['description_zh_hans']
                messages.info(request, _('Traducción automática aplicada. Revisa los campos en chino.'))
            except Exception as e:
                messages.warning(request, _('No se pudo traducir automáticamente: %(error)s') % {'error': str(e)})
        
        super().save_model(request, obj, form, change)

