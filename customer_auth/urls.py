from django.urls import path

from .views import *

urlpatterns = [
    path('customer/change_name/', change_name),
    path('customer/change_password/', change_password),
    path('customer/change_phone/', change_phone),
    path('customer/very_and_edit/', editPhone_OTP.as_view()),
    path('customer/edit_resend_otp/', resend_phone_otp)

]