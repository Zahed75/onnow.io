from django.template.defaulttags import url
from django.urls import path, include, re_path

from .views import *
from rest_framework import routers

router = routers.DefaultRouter()

router.register('live_order',GetLiveOrderView,basename='live_order')
router.register('order_history', GetOrderHistory, basename='order_history')
router.register('customer/order', CustomerOrders, basename='customer_order')
router.register('place_order',PlaceOrder)
router.register('notification', GetNotification, basename='notification')

urlpatterns = router.urls



urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard),
    path('dashboard/<str:brand>/', dashboard),
    re_path(r'^dashboard_channel/$', sourceCount),
    path('paynow/', paynow),
    path('edit_live_order/<str:order_id>/', editLiveOrder)
]
