from django.urls import path

from products.views import RetrieveUpdateDeleteProductView, CreateListProductView, AddOrRemoveFromWishlistView, \
    WishlistView

urlpatterns = [
    path('detail/<str:product_slug>/', RetrieveUpdateDeleteProductView.as_view(), name="product-detail"),
    path('shop/', CreateListProductView.as_view(), name="shop"),

    path('shop-by-category/<str:category_name>/', CreateListProductView.as_view(), name="shop-by-category"),
    path('shop-by-subcategory/<str:subcategory_name>/', CreateListProductView.as_view(), name="shop-by-subcategory"),
    path('shop-by-tag/<str:tag_name>/', CreateListProductView.as_view(), name="shop-by-tag"),

    path('wishlist/', WishlistView.as_view(), name="wishlist"),

    path('wishlist/add-or-remove/', AddOrRemoveFromWishlistView.as_view(), name='add-remove-from-wishlist'),

]
