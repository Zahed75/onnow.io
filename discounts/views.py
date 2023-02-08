import re
from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from brands.models import Brand
from discounts.models import Discount
from users.models import Owner, Manager
from .serializers import (
    ListDiscountSerializer, BrandWiseDiscountListSerializer,
    DiscountSerializer,
)
from utils.custom_mixin import GetSerializerClassMixin


class DiscountAPIView(GetSerializerClassMixin, viewsets.ModelViewSet):
    serializer_class = ListDiscountSerializer
    permission_classes = [IsAuthenticated]
    queryset = Discount.objects.all()

    serializer_action_classes = {
        'list': ListDiscountSerializer,
        'retrieve': BrandWiseDiscountListSerializer,
        'create': DiscountSerializer,
        'partial_update': DiscountSerializer
    }

    def retrieve(self, request, *args, **kwargs):
        
        try:
            if request.user.user_type == 'ACO':
                OWNER = Owner.objects.get(user=request.user)
                BRAND = Brand.objects.get(id=kwargs['pk'], owner=OWNER)
            elif request.user.user_type == 'MGR':
                MANAGER = Manager.objects.get(user=request.user)
                BRAND = Brand.objects.get(id=kwargs['pk'], manager=MANAGER)
            else:
                return Response({
                'errors': 'You do not have access to this service!',
                'server_error': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)
            
            discount_objs = Discount.objects.filter(brand=BRAND)
            serializer = self.get_serializer(BRAND)

            return Response({
                'data': serializer.data,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'errors': 'Bad Request!',
                'server_error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except:
            return Response({
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        try:
            if request.user.user_type == 'ACO':
                OWNER = Owner.objects.get(user=request.user)
                BRAND = Brand.objects.get(id=request.data['brand'], owner=OWNER)
            elif request.user.user_type == 'MGR':
                MANAGER = Manager.objects.get(user=request.user)
                BRAND = Brand.objects.get(id=request.data['brand'], manager=MANAGER)
            else:
                return Response({
                'errors': 'You do not have access to this service!',
            }, status=status.HTTP_401_UNAUTHORIZED)
            print(request.data)
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response({
                'message': 'Discount Added!',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'errors': 'Bad Request!',
                'server_error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        

    def update(self, request, *args, **kwargs):
        try:
            discount_obj = self.get_object()
            can_update = False
            if request.user.user_type == 'ACO':
                OWNER = Owner.objects.get(user=request.user)
                can_update = Brand.objects.filter(id=discount_obj.brand.id, owner=OWNER).exists()
            elif request.user.user_type == 'MGR':
                MANAGER = Manager.objects.get(user=request.user)
                can_update = Brand.objects.filter(id=discount_obj.brand.id, manager=MANAGER).exists()
            else:
                return Response({
                'errors': 'You do not have access to this service!',
            }, status=status.HTTP_401_UNAUTHORIZED)

            if can_update:
                serializer = self.get_serializer(instance=discount_obj, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response({
                'message': 'Discount updated!',
                'data': serializer.data,
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                'message': 'You can not update this object!',
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        except Exception as e:
            return Response({
                'errors': 'Bad Request!',
                'server_error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        

    def destroy(self, request, *args, **kwargs):
        try:
            discount = self.get_object()
            can_update = False
            if request.user.user_type == 'ACO':
                OWNER = Owner.objects.get(user=request.user)
                can_update = Brand.objects.filter(id=discount.brand.id, owner=OWNER).exists()
            elif request.user.user_type == 'MGR':
                MANAGER = Manager.objects.get(user=request.user)
                can_update = Brand.objects.filter(id=discount.brand.id, manager=MANAGER).exists()
            else:
                return Response({
                'errors': 'You can not delete this object!',
            }, status=status.HTTP_401_UNAUTHORIZED)

            if can_update:
                discount.delete()
                return Response({
                    'message': 'Discount deleted!'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'message': 'You can not delete this object!'
                }, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            return Response({
                'errors': 'Outlet not found!',
                'server_error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class AddPromoCodeAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        
        try:
            promo_code = request.data['promo_code']
            subtotal = float(request.data['subtotal'])
            discount_obj = Discount.objects.get(promo_code__exact=promo_code)

            if subtotal >= discount_obj.minimum_spend and subtotal <= discount_obj.maximum_spend:
                discounted = subtotal * float(discount_obj.discount_amount) / 100
                return Response({
                    'data': str(discounted),
                    'message': 'Discount added!',
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'message': 'Discount not applicable!'
                }, status=status.HTTP_200_OK)

        except:
            return Response({
                'errors': 'Enter a valid promo code!'
            }, status=status.HTTP_400_BAD_REQUEST)


