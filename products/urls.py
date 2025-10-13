from django.urls import path

from products.views import RetrieveUpdateDeleteProductView, AddOrRemoveFromWishlistView, \
    WishlistView, ListProductView, CreateProductView, CreateCategoryView

urlpatterns = [
    path('detail/<str:product_slug>/', RetrieveUpdateDeleteProductView.as_view(), name="product-detail"),
    path('shop/', ListProductView.as_view(), name="shop"),
    path('add-product/', CreateProductView.as_view(), name="add-product"),
    path('add-category/', CreateCategoryView.as_view(), name="add-category"),

    path('shop-by-category/<str:category_name>/', ListProductView.as_view(), name="shop-by-category"),
    path('shop-by-subcategory/<str:subcategory_name>/', ListProductView.as_view(), name="shop-by-subcategory"),
    path('shop-by-tag/<str:tag_name>/', ListProductView.as_view(), name="shop-by-tag"),

    path('wishlist/', WishlistView.as_view(), name="wishlist"),

    path('wishlist/add-or-remove/', AddOrRemoveFromWishlistView.as_view(), name='add-remove-from-wishlist'),

]
