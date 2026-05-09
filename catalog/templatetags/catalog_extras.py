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
        ('sandwich', ('sandwich', 'sandwitch', 'emparedado', 'maxi')),
        ('salchichas', ('salchicha', 'frankfurt', 'viena', 'hot dog', 'fuet')),
        ('pizzas', ('pizza', 'masa')),
        ('jamon', ('jamon', 'jamón', 'serrano', 'cocido', 'york', 'bodega', 'iberico', 'chorizo', 'salchichon', 'lomo')),
        ('pavo', ('pavo', 'pechuga', 'pollo', 'turkey', 'chicken')),
    )

    for slug, keywords in mappings:
        if any(keyword in haystack for keyword in keywords):
            return slug

    return 'todos'


@register.filter
def product_category_slugs(product):
    """Devuelve todos los slugs de categorías aplicables como string separado por comas."""
    if product is None:
        return 'todos'

    source = (getattr(product, 'name_es', '') or getattr(product, 'name_zh_hans', '')).lower()
    description = (getattr(product, 'description_es', '') or getattr(product, 'description_zh_hans', '')).lower()
    haystack = f"{source} {description}".strip()

    mappings = (
        ('sandwich', ('sandwich', 'sandwitch', 'emparedado', 'maxi')),
        ('salchichas', ('salchicha', 'frankfurt', 'viena', 'hot dog', 'fuet')),
        ('pizzas', ('pizza', 'masa')),
        ('jamon', ('jamon', 'jamón', 'serrano', 'cocido', 'york', 'bodega', 'iberico', 'chorizo', 'salchichon', 'lomo')),
        ('pavo', ('pavo', 'pechuga', 'pollo', 'turkey', 'chicken')),
    )

    found = []
    for slug, keywords in mappings:
        if any(keyword in haystack for keyword in keywords):
            found.append(slug)

    if not found:
        return 'todos'

    return ','.join(found)
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


@register.filter
def product_brand(product):
    """Intenta derivar la marca del producto a partir de su nombre."""
    if product is None:
        return ''
    name = (getattr(product, 'name_es', '')).lower()
    
    brands = [
        ('Oscar Mayer', ('oscar mayer', 'mayer')),
        ('El Pozo', ('el pozo', 'elpozo')),
        ('Campofrío', ('campofrio', 'campofrío')),
        ('Revilla', ('revilla',)),
        ('Argal', ('argal',)),
        ('Navidul', ('navidul',)),
        ('Casademont', ('casademont',)),
        ('Palacios', ('palacios',)),
        ('Fenix', ('fenix', 'fénix')),
    ]
    
    for brand_name, keywords in brands:
        if any(keyword in name for keyword in keywords):
            return brand_name
            
    # Fallback: primera palabra
    words = getattr(product, 'name_es', '').split()
    if words:
        return words[0]
    return 'Fenix'


@register.filter
def product_type_display(product):
    """Devuelve el nombre legible del tipo de producto para las migas de pan."""
    if product is None:
        return ''
    slug = product_type(product)
    
    if slug == 'otros':
        cat_slug = product_category(product)
        if cat_slug == 'sandwich': return 'Sándwich'
        if cat_slug == 'pizzas': return 'Pizzas'
        return 'Charcutería'

    types_map = {
        'charcuteria': 'Charcutería',
        'curados': 'Curados',
        'ibericos': 'Ibéricos',
        'jamon-cocido': 'Jamón Cocido y York',
        'jamon-curado': 'Jamón Curado',
        'pavo': 'Pavo y Pollo',
        'platos-preparados': 'Platos Preparados',
        'salchichas': 'Salchichas',
        'sandwich': 'Sándwich',
        'pizzas': 'Pizzas',
    }
    return types_map.get(slug, 'Charcutería')
