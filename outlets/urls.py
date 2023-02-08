from django.urls import path, include
from rest_framework import routers
from .views import *

router = routers.DefaultRouter()

router.register('api/outlets', OutletView, basename='outlet')
router.register('api/outlet_by_name', GetOutletbyName)

urlpatterns = [
    path('', include(router.urls)),
    path('api/outlets/approve/<pk>/', ApproveOutletView.as_view(), name='approve-outlet'),
    path('api/outlets/details/<pk>/', GetOutletDetailsView.as_view(), name='outlet-details'),
    path('api/outlet-owner-info/<pk>/', GetCandidateInfo.as_view(), name='outletOwner_info'),
    path('api/outlets-by-area/<pk>/', GetOutletsbyDeliveryAddress.as_view(), name='outlets_by_id'),
]
