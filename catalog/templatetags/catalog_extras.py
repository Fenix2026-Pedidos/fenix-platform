from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Obtiene un item de un diccionario usando una clave"""
    if dictionary is None:
        return 0
    # Convertir key a string porque el carrito usa strings como keys
    key_str = str(key)
    return dictionary.get(key_str, 0)


@register.filter
def product_category(product):
    """Deriva la categoría pública del producto para los tabs del catálogo."""
    if product is None:
        return 'todos'

    source = (getattr(product, 'name_es', '') or getattr(product, 'name_zh_hans', '')).lower()
    description = (getattr(product, 'description_es', '') or getattr(product, 'description_zh_hans', '')).lower()
    haystack = f"{source} {description}".strip()

    mappings = (
        ('packs', ('pack', 'combo', 'lote', 'surtido', 'ahorro')),
        ('jamon-curado', ('curado', 'serrano', 'bodega', 'reserva', 'gran reserva', 'iberico')),
        ('jamon-cocido', ('cocido', 'york', 'dulce', 'extra')),
        ('pavo', ('pavo', 'turkey', 'pechuga', 'pollo', 'chicken')),
    )

    for slug, keywords in mappings:
        if any(keyword in haystack for keyword in keywords):
            return slug

    return 'todos'
@register.filter
def product_type(product):
    """Deriva el tipo de producto para los filtros laterales."""
    if product is None:
        return 'todos'
    
    haystack = f"{getattr(product, 'name_es', '')} {getattr(product, 'description_es', '')}".lower()
    
    # Mapeo de tipos (coincide con los radio buttons en product_list.html)
    types = (
        ('charcuteria', ('charcuteria', 'embutido', 'fiambre')),
        ('curados', ('lomo', 'chorizo', 'salchichon')),
        ('ibericos', ('iberico', 'bellota', 'cebo')),
        ('jamon-cocido', ('cocido', 'york', 'dulce')),
        ('jamon-curado', ('curado', 'serrano', 'bodega')),
        ('pavo', ('pavo', 'pollo', 'turkey', 'chicken')),
        ('platos-preparados', ('plato', 'preparado', 'listo', 'cocinado', 'frankfurt')),
        ('salchichas', ('salchicha', 'frankfurt', 'viena')),
    )
    
    for slug, keywords in types:
        if any(keyword in haystack for keyword in keywords):
            return slug
            
    return 'otros'


@register.filter
def product_features(product):
    """Deriva las características especiales del producto."""
    if product is None:
        return ''
    
    haystack = f"{getattr(product, 'name_es', '')} {getattr(product, 'description_es', '')}".lower()
    found = []
    
    # Mapeo de características (coincide con checkboxes en product_list.html)
    features = (
        ('sin-lactosa', ('sin lactosa', 'no lactose', 'lactosa')),
        ('sin-conservantes', ('sin conservantes', 'no preservatives')),
        ('sin-colorantes', ('sin colorantes', 'no artificial colors')),
        ('sin-azucares', ('sin azucares', 'sin azúcar', 'no sugar')),
        ('bajo-carbohidratos', ('bajo en carb', 'low carb', 'keto')),
        ('apto-diabeticos', ('diabetico', 'apto para diabeticos')),
        ('natural', ('natural', 'artesano', 'tradicional')),
    )
    
    for slug, keywords in features:
        if any(keyword in haystack for keyword in keywords):
            found.append(slug)
            
    return ','.join(found)
