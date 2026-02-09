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
        ('packs', ('pack', 'combo', 'lote')),
        ('jamon-curado', ('curado', 'serrano', 'bodega')),
        ('jamon-cocido', ('cocido', 'york', 'dulce')),
        ('pavo', ('pavo', 'turkey', 'pechuga')),
    )

    for slug, keywords in mappings:
        if any(keyword in haystack for keyword in keywords):
            return slug

    return 'todos'
