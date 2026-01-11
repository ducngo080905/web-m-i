from .cart import Cart

def cart_context(request):
    """Add cart to all templates"""
    return {'cart': Cart(request)}