
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('', include('products.urls')),
    path('', include('crm.urls')),
    path('', include('cart.urls')),
    path('', include('payments.urls')),
    path('api/', include('api.urls')),
]
