from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
import logging
from .models import Product, PromotionalProduct

@admin.register(PromotionalProduct)
class PromotionalProductAdmin(admin.ModelAdmin):
    list_display = ('promo_title', 'product', 'promo_label', 'display_order', 'is_active', 'start_date', 'end_date')
    list_filter = ('is_active', 'promo_label', 'start_date', 'end_date')
    search_fields = ('promo_title', 'product__name_es')
    autocomplete_fields = ['product']  # Hace que el desplegable sea un buscador
    ordering = ('display_order', '-created_at')
    readonly_fields = ('image_preview', 'display_price_admin', 'display_unit_admin')
    
    fieldsets = (
        (None, {
            'fields': (
                'product', 
                'promo_title', 
                'promo_image', 
                'image_preview', 
                ('display_price_admin', 'display_unit_admin'),
                'promo_label', 
                'promo_type', 
                'target_category', 
                'target_query'
            )
        }),
        (_('Configuración de visualización'), {
            'fields': ('display_order', 'is_active', 'start_date', 'end_date')
        }),
    )

    def image_preview(self, obj):
        url = obj.display_image_url
        if url:
            return mark_safe(f'<img src="{url}" style="max-height: 200px; border-radius: 8px;" />')
        return _("Sin imagen")
    image_preview.short_description = _("Vista previa (Heredada/Manual)")

    def display_price_admin(self, obj):
        if not obj.product: return "-"
        return f"{obj.display_price} €"
    display_price_admin.short_description = _("Precio heredado")

    def display_unit_admin(self, obj):
        if not obj.product: return "-"
        return obj.display_unit
    display_unit_admin.short_description = _("Unidad heredada")
from .utils import translate_product_fields

logger = logging.getLogger(__name__)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'reference', 'name_es', 'price', 'unit_display', 'stock_available',
        'promo_label', 'is_active',
    )
    list_filter = ('promo_label', 'stock_status', 'is_active', 'is_new', 'is_best_seller', 'is_offer')
    search_fields = ('name_es', 'name_zh_hans', 'reference')
    actions = ['batch_generate_ai_descriptions']
    readonly_fields = (
        'stock_status', 'created_at', 'image_preview', 'translate_button', 'generate_desc_button',
        'description_ai_generated', 'description_source', 'description_last_generated_at'
    )
    fieldsets = (
        (None, {'fields': ('reference', 'name_es', 'name_zh_hans', 'description_es', 'description_zh_hans', 'translate_button', 'generate_desc_button', 'image', 'image_preview', 'price', 'unit_display', 'is_active')}),
        (_('Metadatos de IA (Solo lectura)'), {
            'classes': ('collapse',),
            'fields': ('description_ai_generated', 'description_source', 'description_last_generated_at')
        }),
        (_('Etiqueta Promocional (Único Sistema)'), {'fields': ('promo_label',)}),
        (_('Stock (solo managers)'), {'fields': ('stock_available', 'stock_min_threshold', 'stock_status')}),
        (_('Etiquetas Especiales (LEGACY - No usar para badges)'), {
            'classes': ('collapse',),
            'fields': ('is_new', 'is_best_seller', 'is_offer'),
            'description': _('Estas etiquetas están obsoletas. Usa el campo "Etiqueta promocional" de arriba.')
        }),
        (_('Auditoría'), {'fields': ('created_at',)}),
    )
    
    def image_preview(self, obj):
        """Muestra una vista previa de la imagen en el admin"""
        if not obj or not obj.image:
            return mark_safe('<span style="color: #999;">Sin imagen</span>')
        
        try:
            # Asegurar que usamos la URL robusta (maneja local y GCS fallback)
            image_url = obj.image_url
            if not image_url:
                return mark_safe('<span style="color: #999;">Sin URL válida</span>')
                
            return format_html(
                '<div style="background: #f8f8f8; padding: 10px; border-radius: 8px; display: inline-block; border: 1px solid #ddd;">'
                '<img src="{}" style="max-width: 150px; max-height: 150px; display: block; margin-bottom: 5px; border-radius: 4px;" />'
                '<a href="{}" target="_blank" style="font-size: 11px; color: #264b5d;">👁️ Ver tamaño completo</a>'
                '</div>',
                image_url, image_url
            )
        except Exception:
            return mark_safe('<span style="color: #ba2121;">Error al cargar vista previa</span>')
    image_preview.short_description = 'Vista previa actual'
    
    def translate_button(self, obj):
        """Botón para traducir automáticamente de español a chino"""
        if not obj or not obj.pk:
            return mark_safe('<span style="color: #666; font-size: 12px;">Guarda el producto primero para habilitar la traducción.</span>')
        
        return mark_safe(
            '<div style="background: #f0f7f9; border: 1px solid #c9e2eb; padding: 12px; border-radius: 6px; max-width: 600px;">'
            '<button type="button" onclick="translateProduct()" class="button" style="'
            'background: #007bff; color: white; border: none; padding: 8px 16px; '
            'border-radius: 4px; cursor: pointer; font-size: 13px; font-weight: 600; margin-bottom: 8px;'
            '">'
            '🌐 Traducir automáticamente (Español → Chino)'
            '</button>'
            '<p style="margin: 0; font-size: 12px; color: #555;">'
            '<strong>¿Cómo funciona?</strong> Esta utilidad usa IA para traducir el <em>Nombre</em> y la <em>Descripción</em> '
            'del español al chino simplificado. Los campos se rellenarán automáticamente y podrás revisarlos antes de guardar.'
            '</p>'
            '</div>'
            '<script>'
            'function translateProduct() {'
            '  var nameEs = document.getElementById("id_name_es").value;'
            '  var descEs = document.getElementById("id_description_es").value;'
            '  if (!nameEs && !descEs) { alert("Completa los campos en español primero."); return; }'
            '  if (!confirm("¿Traducir nombre y descripción al chino?")) return;'
            '  var btn = event.target; btn.textContent = "⌛ Traduciendo..."; btn.disabled = true;'
            '  var currentPath = window.location.pathname;'
            '  var translateUrl = currentPath.endsWith("/") ? currentPath + "translate/" : currentPath + "/translate/";'
            '  fetch(translateUrl, {'
            '    method: "POST",'
            '    headers: { "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value, "Content-Type": "application/x-www-form-urlencoded" },'
            '    body: "name_es=" + encodeURIComponent(nameEs) + "&description_es=" + encodeURIComponent(descEs)'
            '  })'
            '  .then(r => r.json())'
            '  .then(data => {'
            '    btn.textContent = "🌐 Traducir automáticamente (Español → Chino)"; btn.disabled = false;'
            '    if (data.success) {'
            '      if (data.name_zh_hans) document.getElementById("id_name_zh_hans").value = data.name_zh_hans;'
            '      if (data.description_zh_hans) document.getElementById("id_description_zh_hans").value = data.description_zh_hans;'
            '    } else { alert("Error: " + (data.error || "No se pudo traducir")); }'
            '  });'
            '}'
            '</script>'
        )
    translate_button.short_description = 'Asistente de Traducción'
    translate_button.allow_tags = True
    
    def get_urls(self):
        """Añade URL de traducción y de generación de descripción por IA"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:object_id>/translate/',
                self.admin_site.admin_view(self.translate_view),
                name='catalog_product_translate',
            ),
            path(
                '<int:object_id>/generate_ai_desc/',
                self.admin_site.admin_view(self.generate_ai_desc_view),
                name='catalog_product_generate_ai_desc',
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
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        """Personalizar etiquetas de campos de archivo para mayor claridad"""
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'image':
            field.widget.clear_checkbox_label = "Eliminar imagen actual"
        return field
    
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

    def generate_desc_button(self, obj):
        """Botón para generar automáticamente la descripción del producto mediante Visión IA"""
        if not obj or not obj.pk:
            return mark_safe(f'<span style="color: #666; font-size: 12px;">{_("Guarda el producto primero para habilitar la generación de descripción.")}</span>')
        
        return mark_safe(
            '<div style="background: #fdf6f0; border: 1px solid #f5e0cf; padding: 12px; border-radius: 6px; max-width: 600px; margin-top: 10px;">'
            '<button type="button" onclick="generateAIDescription()" class="button" style="'
            'background: #e67e22; color: white; border: none; padding: 8px 16px; '
            'border-radius: 4px; cursor: pointer; font-size: 13px; font-weight: 600; margin-bottom: 8px;'
            '">'
            '✨ Generar descripción con Visión IA (OCR)'
            '</button>'
            '<p style="margin: 0; font-size: 12px; color: #555;">'
            '<strong>¿Cómo funciona?</strong> Esta utilidad usa <strong>Gemini 2.5 Flash</strong> para analizar '
            'visualmente el envase en la imagen, extraer marcas/textos y redactar una descripción comercial premium. '
            'También se traducirá al chino automáticamente. Los textos resultantes se insertarán para tu revisión antes de guardar el formulario.'
            '</p>'
            '</div>'
            '<script>'
            'function generateAIDescription() {'
            '  var btn = event.target; btn.textContent = "⌛ Analizando envase..."; btn.disabled = true;'
            '  var currentPath = window.location.pathname;'
            '  var parts = currentPath.split("/");'
            '  var changeIndex = parts.indexOf("change");'
            '  var baseAdminPath = "";'
            '  if (changeIndex !== -1) {'
            '    baseAdminPath = parts.slice(0, changeIndex).join("/") + "/";'
            '  } else {'
            '    baseAdminPath = currentPath.endsWith("/") ? currentPath : currentPath + "/";'
            '  }'
            '  var generateUrl = baseAdminPath + "generate_ai_desc/";'
            '  fetch(generateUrl, {'
            '    method: "POST",'
            '    headers: { "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value }'
            '  })'
            '  .then(r => r.json())'
            '  .then(data => {'
            '    btn.textContent = "✨ Generar descripción con Visión IA (OCR)"; btn.disabled = false;'
            '    if (data.success) {'
            '      if (data.description_es) document.getElementById("id_description_es").value = data.description_es;'
            '      if (data.description_zh_hans) document.getElementById("id_description_zh_hans").value = data.description_zh_hans;'
            '      alert("¡Descripción generada y traducida con éxito! Revisa los cambios y haz clic en Guardar.");'
            '    } else { alert("Error: " + (data.error || "No se pudo generar")); }'
            '  })'
            '  .catch(err => {'
            '    btn.textContent = "✨ Generar descripción con Visión IA (OCR)"; btn.disabled = false;'
            '    alert("Error de conexión: " + err);'
            '  });'
            '}'
            '</script>'
        )
    generate_desc_button.short_description = 'Asistente de Descripción IA'
    generate_desc_button.allow_tags = True

    def generate_ai_desc_view(self, request, object_id):
        """Vista para generar descripción del producto usando Visión IA"""
        from django.http import JsonResponse
        from django.utils import timezone
        from ai_assistant.description_generator import DescriptionGenerator
        
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
        
        try:
            product = Product.objects.get(pk=object_id)
            result = DescriptionGenerator.generate_and_translate_for_product(product)
            
            desc_es = result.get('description_es', '')
            desc_zh = result.get('description_zh_hans', '')
            
            if desc_es:
                product.description_ai_generated = True
                product.description_source = 'image_ocr' if product.image else 'ai_enriched'
                product.description_last_generated_at = timezone.now()
                product.save()
                
                return JsonResponse({
                    'success': True,
                    'description_es': desc_es,
                    'description_zh_hans': desc_zh,
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'No se pudo generar una descripción válida'
                })
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Producto no encontrado'
            })
        except Exception as e:
            import traceback
            logger.error(f"Error en generación AI de descripción: {traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    def batch_generate_ai_descriptions(self, request, queryset):
        """Acción en lote para generar descripciones mediante Visión IA"""
        from django.utils import timezone
        from ai_assistant.description_generator import DescriptionGenerator
        
        success_count = 0
        error_count = 0
        
        for product in queryset:
            desc_empty = (
                not product.description_es or 
                product.description_es.strip() == "" or 
                "Sin descripción disponible" in product.description_es
            )
            
            if desc_empty:
                try:
                    result = DescriptionGenerator.generate_and_translate_for_product(product)
                    desc_es = result.get('description_es', '')
                    desc_zh = result.get('description_zh_hans', '')
                    
                    if desc_es:
                        product.description_es = desc_es
                        product.description_zh_hans = desc_zh
                        product.description_ai_generated = True
                        product.description_source = 'image_ocr' if product.image else 'ai_enriched'
                        product.description_last_generated_at = timezone.now()
                        product.save()
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error generando descripción en lote para {product.name_es}: {e}")
                    error_count += 1
                    
        self.message_user(
            request,
            _(f"Se han generado {success_count} descripciones con IA de forma exitosa. {error_count} errores.")
        )
    batch_generate_ai_descriptions.short_description = "✨ Generar descripción con IA (solo vacíos)"

