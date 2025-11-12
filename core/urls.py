
from django.contrib import admin
from django.urls import path, include
import os

app_name = os.getenv('APP_NAME')

admin.site.site_header = f"{app_name} Administration"
admin.site.site_title = f"{app_name} Admin Portal"
admin.site.index_title = f"Welcome to {app_name} Admin Dashboard"


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('', include('products.urls')),
    path('', include('crm.urls')),
    path('', include('cart.urls')),
    path('', include('payments.urls')),
    path('api/', include('api.urls')),
]


handler404 = "crm.views.page_not_found"
handler500 = "crm.views.server_error"