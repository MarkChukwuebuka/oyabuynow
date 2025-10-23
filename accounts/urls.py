from django.urls import path

from accounts.views import UserLoginView, UserSignupView, UserDashboardView, UserLogoutView, UpdateUserView, \
    UserForgotPasswordView, VendorDashboardView, OnboardVendorView, VendorProductListView, VendorOrdersView, \
    VendorProfileView, VerifyOtpView, CreateNewPasswordView

urlpatterns = [
    path('login/', UserLoginView.as_view(), name="login"),
    path('logout/', UserLogoutView.as_view(), name="logout"),
    path('signup/', UserSignupView.as_view(), name="signup"),
    path('forgot-password/', UserForgotPasswordView.as_view(), name="forgot-password"),
    path('verify-otp/', VerifyOtpView.as_view(), name="verify-otp"),
    path('create-new-password/', CreateNewPasswordView.as_view(), name="create-new-password"),

    path('dashboard/', UserDashboardView.as_view(), name="dashboard"),
    path('settings/', UpdateUserView.as_view(), name="settings"),


    path('onboard-vendor/', OnboardVendorView.as_view(), name="onboard-vendor"),
    path('vendor/home/', VendorDashboardView.as_view(), name="vendor-dashboard-home"),
    path('vendor/products/', VendorProductListView.as_view(), name="vendor-dashboard-products"),
    path('vendor/orders/', VendorOrdersView.as_view(), name="vendor-dashboard-orders"),
    path('vendor/profile/', VendorProfileView.as_view(), name="vendor-dashboard-profile"),

]
