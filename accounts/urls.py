from django.urls import path

from accounts.views import UserLoginView, UserSignupView, UserDashboardView, UserLogoutView, UpdateUserView, \
    UserForgotPasswordView, VendorDashboardView, OnboardVendorView

urlpatterns = [
    path('login/', UserLoginView.as_view(), name="login"),
    path('logout/', UserLogoutView.as_view(), name="logout"),
    path('signup/', UserSignupView.as_view(), name="signup"),
    path('forgot-password/', UserForgotPasswordView.as_view(), name="forgot-password"),
    path('create-new-password/', UserForgotPasswordView.as_view(), name="create-new-password"),

    path('dashboard/', UserDashboardView.as_view(), name="dashboard"),


    path('onboard-vendor/', OnboardVendorView.as_view(), name="onboard-vendor"),
    path('vendor-dashboard/', VendorDashboardView.as_view(), name="vendor-dashboard"),
    path('settings/', UpdateUserView.as_view(), name="settings"),
]
