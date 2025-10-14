from django.urls import path
from payments.views import check_out, CreateListOrderView, RetrieveUpdateDeleteOrderView, paystack_verify_payment, \
    ConfirmOrderView

urlpatterns = [
    path('checkout/', check_out, name='checkout'),
    path('confirm-order/', ConfirmOrderView.as_view(), name='confirm-order'),
    path('payment-status/<int:order_id>/', ConfirmOrderView.as_view(), name='payment-status'),
    path('orders/', CreateListOrderView.as_view(), name='orders'),
    path('order/<str:ref>/', RetrieveUpdateDeleteOrderView.as_view(), name='order-detail'),
    path('paystack-verify-payment/<int:order_id>/', paystack_verify_payment, name='paystack-verify-payment'),
]
