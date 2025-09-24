from django.urls import path
from cart.views import add_to_cart, cart, update_cart

urlpatterns = [
    path('cart/', cart, name='cart'),
    path('add_to_cart/', add_to_cart, name='add_to_cart'),
    path('update_cart/', update_cart, name='update_cart'),
]