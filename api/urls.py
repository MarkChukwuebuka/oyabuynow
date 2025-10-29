from django.urls import path
from accounts.views import check_email, get_banks, verify_bank_account, resend_otp
from crm.elasticsearch_views import ProductSearchView, ProductAutocompleteView, ProductFacetsView, SimilarProductsView, \
    CategorySearchView, BrandSearchView
from crm.views import search_suggestions
from media.views import delete_product_image
from products.views import get_subcategories
from search.views import autocomplete_search

urlpatterns = [
    path("check-email/", check_email, name="check_email"),
    path("get-banks/", get_banks, name="get-banks"),
    path("verify-bank-account/", verify_bank_account, name="verify-bank-account"),
    path("get-subcategories/<int:category_id>/", get_subcategories, name='get-subcategories'),
    path("delete-product-image/<int:upload_id>/", delete_product_image, name='delete-product-image'),
    path("resend-otp/", resend_otp, name='resend-otp'),
    path("search-suggestions/", search_suggestions, name='search-suggestions'),

    #elastic search endpoints
    path('search/autocomplete/', autocomplete_search, name='autocomplete-search'),
    # path('search/products/', ProductSearchView.as_view(), name='product_search'),
    # path('search/autocomplete/', ProductAutocompleteView.as_view(), name='autocomplete'),
    # path('search/facets/', ProductFacetsView.as_view(), name='facets'),
    # path('search/similar/<int:product_id>/', SimilarProductsView.as_view(), name='similar_products'),
    #
    # # Category and brand search
    # path('search/categories/', CategorySearchView.as_view(), name='category_search'),
    # path('search/brands/', BrandSearchView.as_view(), name='brand_search'),
]
