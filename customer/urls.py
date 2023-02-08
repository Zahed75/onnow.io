from django.urls import path, include
from rest_framework import routers

from .views import *
#
router = routers.DefaultRouter()

router.register('delivery_address',DeliveryAddressCRUD, basename='delivery_address')


urlpatterns = [
    path('api/customer/', include(router.urls)),
    path('api/customers/<pk>/', CustomerAPIView.as_view(), name='customers'),
]