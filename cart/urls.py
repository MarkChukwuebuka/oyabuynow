from django.urls import path
from cart.views import add_to_cart, cart, update_cart, remove_from_cart

urlpatterns = [
    path('cart/', cart, name='cart'),
    path('api/add_to_cart/', add_to_cart, name='add_to_cart'),
    path('api/remove_from_cart/', remove_from_cart, name='remove_from_cart'),
    path('api/update_cart/', update_cart, name='update_cart'),
]