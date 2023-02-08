# from django.conf.urls import url
from django.urls import include, path
from rest_framework import routers

from outlets.views import *

from .views import *

# from rest_framework_swagger.renderers import SwaggerUIRenderer, OpenAPIRenderer




router = routers.DefaultRouter()
# router.register(r"api/user",UserProfileViewSet),
router.register('user', UserViewsets)
router.register('api/brand-manager', BrandManagerView, basename='brand_manager')
router.register('api/outlet-manager', OutletManagerView, basename='outlet_manager')
# router.register('edit-profile', EditUserView, basename='edit_user')

urlpatterns = [

    # for registration, OTP verification and authentication
    path('', include(router.urls)),
    path('api/user-register/', RegisterView.as_view()),
    
    # brand manager updating url - primary
    path('api/brand-manager-update/<int:id>/', update_brand_manager),
    # brand manager updating url - primary
    path('api/outlet-manager-update/<int:id>/', update_outlet_manager),

    # path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
   
    path('api/customer-register/', CustomerRegisterView.as_view()),

    path('api/token/', OnnowTokenObtainPairView.as_view()),

    path('api/tokenVerify/', TokenVerify.as_view()),
    path('api/token/refresh/', TokenRefresh.as_view()),

    path('api/email-verify/', VerifyEmail.as_view()),
    path('api/phone-verify/', VerifyPhone.as_view()),

    path('api/resend_otp/', resend_otp),
    path('api/resend_phone_otp/', resend_phone_otp),

    # for password reset with OTP
    path('api/forgot_passowd/', RequestPasswordResetEmail.as_view()),
    path('api/check_forgot_password_otp/', CheckForgotPasswordOtp.as_view()),
    path('api/reset_password/', ResetPassword.as_view()),
    # admin pass change in logged in
    path('api/change-password/', ChangePasswordView.as_view(), name='change-password'),

    # for customer password reset with OTP
    path('api/customer_forgot_passowd/', resend_phone_otp),
    path('api/check_customer_forgot_password_otp/', CheckCustomerForgotPasswordOtp.as_view()),
    path('api/reset_customer_password/', ResetCustomerPassword.as_view()),

    # ========customer-EditProfile=========


    # to active account via email link and set new password
    path('api/invite/', ActivateProfileView.as_view(), name='activate-profile'),
    # path('api/new-password/', SetNewPasswordView.as_view(), name='new-password'),

    # edit profile (get n patch)
    path('api/edit-profile/', EditUserView.as_view(), name='edit-profile'),
    path('api/edit-profile/<pk>/', EditUserView.as_view(), name='edit-profile'),
    path('api/change-email/', ChangeEmail.as_view(), name='change_email'),
    path('api/verify-changed-email/', VerifyChangedEmail.as_view(), name='verify_changed_email'),

    path(r'api/logout/', Logout.as_view()),

]
