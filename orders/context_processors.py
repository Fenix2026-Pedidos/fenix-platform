def cart_count(request):
    """Context processor para añadir el contador del carrito a todos los templates"""
    cart = request.session.get('cart', {})
    count = sum(int(qty) for qty in cart.values())
    return {'cart_count': count}
