from django.urls import path
from . import views
from payments.views import start_order, CreateListOrderView, RetrieveUpdateDeleteOrderView

urlpatterns = [
    path('order/', start_order, name='start_order'),
    path('my-orders/', CreateListOrderView.as_view(), name='my-orders'),
    path('order/<str:ref>/', RetrieveUpdateDeleteOrderView.as_view(), name='order-detail'),


]
