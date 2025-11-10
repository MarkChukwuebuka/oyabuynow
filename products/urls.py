from django.urls import path

from products.views import RetrieveProductView, AddOrRemoveFromWishlistView, \
    WishlistView, ListProductView, CreateProductView, CreateCategoryView, UpdateDeleteProductView, delete_product, \
    VendorProductView, ListProductByVendorView, ProductSearchView, ProductDealsView

urlpatterns = [
    path('detail/<str:product_slug>/', RetrieveProductView.as_view(), name="product-detail"),
    path('update-product/<int:product_id>/', UpdateDeleteProductView.as_view(), name="update-product"),
    path('delete-product/<int:product_id>/', delete_product, name="delete-product"),
    path('shop/', ListProductView.as_view(), name="shop"),
    path('deals/', ProductDealsView.as_view(), name="deals"),
    path('add-product/', CreateProductView.as_view(), name="add-product"),
    path('add-category/', CreateCategoryView.as_view(), name="add-category"),

    path('shop-by-category/<str:category_name>/', ListProductView.as_view(), name="shop-by-category"),
    path('shop-by-subcategory/<str:subcategory_name>/', ListProductView.as_view(), name="shop-by-subcategory"),
    path('shop-by-tag/<str:tag_name>/', ListProductView.as_view(), name="shop-by-tag"),
    path('vendor-store/<str:vendor_id>/', ListProductByVendorView.as_view(), name="vendor-store"),

    path('wishlist/', WishlistView.as_view(), name="wishlist"),

    path('wishlist/add-or-remove/', AddOrRemoveFromWishlistView.as_view(), name='add-remove-from-wishlist'),

    path('vendor/<str:product_slug>/', VendorProductView.as_view(), name="vendor-product-detail"),

    path("search/", ProductSearchView.as_view(), name='search'),

]
