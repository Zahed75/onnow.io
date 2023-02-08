from django.contrib.auth import get_user_model

from rest_framework import generics, viewsets, views
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework_simplejwt.authentication import JWTAuthentication
from brands.models import Brand

from users.serializers import UserSerializer

from .models import Customer, DeliveryAddress
from brands.models import Outlet
from orders.models import Order
from users.models import Owner, Manager
from .serializers import CustomerSerializer, ReadAddressSerializer, AddressSerializer
from .filters import CustomerFilter

from utils.custom_permission import IsCustomer
from utils.custom_mixin import PermissionPolicyMixin, GetSerializerClassMixin

User = get_user_model()

class CustomerAPIView(views.APIView):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, requests, *args, **kwargs):
        
        try:
            q_params = self.request.query_params
            is_your_brand = False
            
            if self.request.user.user_type == 'ACO':
                owner = Owner.objects.get(user=self.request.user)
                is_your_brand = Brand.objects.filter(id=kwargs['pk'], owner=owner).exists()
            elif self.request.user.user_type == 'MGR':
                manager = Manager.objects.get(user=self.request.user)
                is_your_brand = Brand.objects.filter(id=kwargs['pk'], manager=manager).exists()

            if is_your_brand:
                brand = Brand.objects.get(id=kwargs['pk'])
                outlets = Outlet.objects.filter(brand=brand)
                if len(q_params) == 0:
                    orders = Order.objects.filter(outlet__in=outlets).distinct('customer')
                else:
                    orders = Order.objects \
                            .filter(outlet__in=outlets) \
                            .filter(customer__user__name__icontains=q_params['name']) \
                            .filter(customer__user__phone_number__icontains=q_params['phone']) \
                            .distinct('customer')
            else:
                return Response({
                    'errors': 'Select your brand!'
                }, status=status.HTTP_401_UNAUTHORIZED)

            # print(orders)
            serializer = self.serializer_class(orders, many=True, context={'outlets': outlets})

            return Response({
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'data': str(e.args[0])
            }, status=status.HTTP_400_BAD_REQUEST)


class DeliveryAddressCRUD(GetSerializerClassMixin, viewsets.ModelViewSet):
    serializer_class = ReadAddressSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsCustomer]

    serializer_action_classes = {
        'create': AddressSerializer,
        'update': AddressSerializer,
        'partial_update': AddressSerializer
    }

    def get_queryset(self, *args, **kwargs):
        current_user = self.request.user
        return DeliveryAddress.objects.filter(customer__user=current_user)

    def perform_create(self, serializer):
        customer = Customer.objects.filter(user=self.request.user).first()
        serializer.save(customer=customer)
