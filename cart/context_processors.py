from cart.services.cart_service import CartService


def cart(request):
    return {'cart': CartService(request)}