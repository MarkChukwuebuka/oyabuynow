from django.urls import path

from products.views import RetrieveUpdateDeleteProductView, CreateListProductView, AddOrRemoveFromWishlistView, \
    WishlistView

urlpatterns = [
    path('<str:product_slug>/', RetrieveUpdateDeleteProductView.as_view(), name="product-detail"),
    path('shop/', CreateListProductView.as_view(), name="shop"),

    path('shop-by-category/<str:name>/', CreateListProductView.as_view(), name="shop-by-category"),
    path('shop-by-subcategory/<str:name>/', CreateListProductView.as_view(), name="shop-by-subcategory"),

    path('wishlist/', WishlistView.as_view(), name="wishlist"),

    path('wishlist/add-or-remove/', AddOrRemoveFromWishlistView.as_view(), name='add-remove-from-wishlist'),

]
