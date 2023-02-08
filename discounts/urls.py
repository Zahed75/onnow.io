from django.urls import path, include
from rest_framework import routers
from .views import *

router = routers.DefaultRouter()

router.register('api/discounts', DiscountAPIView, basename='discounts')

urlpatterns = [
    path('', include(router.urls)),
    path('api/add_promo/', AddPromoCodeAPI.as_view(), name='add_promo'),
]
