def cart_count(request):
    """
    Retorna el número de productos distintos (líneas) en el carrito.
    Ejemplo: 3 Croissants + 2 Jamones = 2 líneas.
    """
    total_lines = 0
    cart = request.session.get('cart', {})
    total_lines = len(cart)
        
    return {
        'cart_count': total_lines
    }

