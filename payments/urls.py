from django.urls import path
from . import views
from payments.views import check_out, CreateListOrderView, RetrieveUpdateDeleteOrderView

urlpatterns = [
    path('check-out/', check_out, name='checkout'),
    path('my-orders/', CreateListOrderView.as_view(), name='my-orders'),
    path('order/<str:ref>/', RetrieveUpdateDeleteOrderView.as_view(), name='order-detail'),


]
