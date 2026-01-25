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
