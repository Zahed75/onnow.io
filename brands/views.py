from django_filters import rest_framework as filters
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import (
    AllowAny, IsAuthenticated
)
from rest_framework.response import Response
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import (
    api_view, permission_classes,
    authentication_classes, parser_classes
)
from rest_framework.parsers import MultiPartParser, JSONParser

from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Q
from users.models import Owner
from utils.custom_permission import IsOwner, IsBrandManager, EditMenu, InventoryHandle, EditItem, IsCustomer
from utils.custom_mixin import PermissionPolicyMixin, GetSerializerClassMixin
from .serializer import *


class BrandCRUD(GetSerializerClassMixin,
                PermissionPolicyMixin,
                viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = ListBrandSerializer
    parser_classes = [JSONParser, MultiPartParser]
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsOwner | IsBrandManager]

    serializer_action_classes = {
        'retrieve': DetailsBrandSerializer,
        'create': CreateBrandSerializer,
        'update': CreateBrandSerializer,
        'partial_update': CreateBrandSerializer
    }

    permission_classes_per_method = {
        'create': [IsOwner]
    }

    def get_queryset(self, *args, **kwargs):
        current_user = self.request.user
        if current_user.user_type == "MGR":
            return Brand.objects.filter(manager__user=current_user)
        else:
            return Brand.objects.all()

    def perform_create(self, serializer):
        owner = Owner.objects.filter(user=self.request.user).first()
        serializer.save(owner=owner)


@parser_classes([MultiPartParser, JSONParser])
class OtherBrand(viewsets.ReadOnlyModelViewSet):
    serializer_class = ListBrandSerializer
    permission_classes = [IsOwner]
    queryset = Brand.objects.all()

    def get_queryset(self, *args, **kwargs):
        current_user = self.request.user
        return Brand.objects.exclude(owner__user=current_user)


@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsOwner])
@parser_classes([MultiPartParser, JSONParser])
def add_other_brand(request):
    data = request.data
    user = request.user
    try:
        benificiary = Owner.objects.filter(user=user).first()
        brand = Brand.objects.filter(subdomain=data["subdomain"]).first()

        if brand.owner != benificiary:
            brand.brand_beneficiary.add(benificiary)
            brand.save()

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Success fully added Brand"
            })
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": str(e)
        })


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@parser_classes([MultiPartParser, JSONParser])
@permission_classes([IsOwner])
def get_all_brand(request):
    user = request.user
    try:
        # my_brands = Brand.objects.filter(Q(owner__user=user) | Q(manager__user=user))
        # other_brands = Brand.objects.filter(brand_beneficiary__user=user)

        if request.user.user_type == "STF":
            # getting outlet managers brands
            brand_ids = Outlet.objects.filter(outlet_manager__user=user).values_list('brand_id', flat=True)
            my_brands = Brand.objects.filter(id__in=brand_ids)
            other_brands = Brand.objects.filter(brand_beneficiary__user=user)
        else:
            my_brands = Brand.objects.filter(Q(owner__user=user) | Q(manager__user=user))
            other_brands = Brand.objects.filter(brand_beneficiary__user=user)


        return Response({
            "code": 200,
            "message": "OK",
            "data": {
                "my_brands": ListBrandSerializer(my_brands, many=True).data,
                "other_brands": ListBrandSerializer(other_brands, many=True).data
            }
        })

    except Exception as e:
        return Response({
            "code": status.HTTP_400_BAD_REQUEST,
            "message": str(e)
        })


class MenuCRUD(PermissionPolicyMixin, viewsets.ModelViewSet):
    serializer_class = CreateMenuSerializer
    queryset = Menu.objects.all()

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    permission_classes_per_method = {
        'create': [IsOwner | IsBrandManager],
        'update': [EditMenu],
        'partial_update': [EditMenu],
        'destroy': [EditMenu]
    }

    def create(self, request, *args, **kwargs):
        try:
            brand = Brand.objects.filter(id=request.data["brand"]).first()

            if request.user == brand.owner.user or brand.manager.all().filter(user=request.user).exists():
                serializer = self.serializer_class(data=request.data)
                if serializer.is_valid():
                    try:
                        menu = Menu.objects.filter(brand=serializer.validated_data.get('brand'),
                                                   name=serializer.validated_data.get('name')).exists()
                        if menu == False:
                            serializer.save()
                            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
                        else:
                            return Response(data={"msg": "Already a menu exists with this name"
                                                  }, status=status.HTTP_400_BAD_REQUEST)
                    except:
                        pass
                else:
                    return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(
                    status=status.HTTP_401_UNAUTHORIZED,
                    data={
                        "msg": "You have no permission to do this action"
                    })
        except:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={
                    "msg": "No Brand found"
                })


class MenuItemCRUD(PermissionPolicyMixin, viewsets.ModelViewSet):
    serializer_class = CreateMenuItemSerializer
    queryset = Item.objects.all()
    parser_classes = [JSONParser, MultiPartParser]

    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    permission_classes_per_method = {
        'create': [IsOwner | IsBrandManager],
        'update': [EditItem],
        'partial_update': [EditItem],
        'destroy': [EditItem]
    }

    def create(self, request, *args, **kwargs):
        try:
            menu = Menu.objects.filter(id=request.data["menu"]).first()

            if request.user == menu.brand.owner.user or menu.brand.manager.all().filter(user=request.user).exists():
                serializer = self.serializer_class(data=request.data)
                if serializer.is_valid():
                    item = Item.objects.filter(menu=serializer.validated_data.get('menu')).filter(
                        name=serializer.validated_data.get('name')).exists()
                    if item == False:
                        serializer.save()
                        return Response(data=serializer.data, status=status.HTTP_201_CREATED)
                    else:
                        return Response(data={"msg": "Already a item exists with this name"
                                              }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(
                    status=status.HTTP_401_UNAUTHORIZED,
                    data={
                        "msg": "Not Authorized to do this action"
                    })
        except:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={
                    "msg": "No Menu found"
                })


class GetInventoryView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    lookup_field = 'outlet__name'
    serializer_class = InventorySr
    queryset = Inventory.objects.all()
    parser_classes = [JSONParser, MultiPartParser]
    authentication_classes = [JWTAuthentication]
    permission_classes = [InventoryHandle]


@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@parser_classes([MultiPartParser, JSONParser])
@permission_classes([InventoryHandle])
def edit_outlet_inventory(request):
    data = request.data
    try:
        serializer = EditInventorySr(data=data)
        if serializer.is_valid():
            inventory = Inventory.objects.get(id=serializer.validated_data.get('id'))
            inventory.is_available = serializer.validated_data.get('is_available')
            inventory.pause_time = serializer.validated_data.get('pause_time')

            inventory.save()

        return Response({
            "status": status.HTTP_200_OK,
            "message": "Successfully Updated"
        })

    except Exception as e:
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": str(e)
        })


@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@parser_classes([MultiPartParser, JSONParser])
@permission_classes([InventoryHandle])
def edit_menu_inventory(request):
    data = request.data
    try:
        serializer = EditInventorySr(data=data)
        if serializer.is_valid():
            menu = InventoryMenu.objects.get(id=serializer.validated_data.get('id'))
            menu.is_available = serializer.validated_data.get('is_available')
            menu.pause_time = serializer.validated_data.get('pause_time')

            menu.save()

        return Response({
            "status": status.HTTP_200_OK,
            "message": "Successfully Updated"
        })

    except Exception as e:
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": str(e)
        })


@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@parser_classes([MultiPartParser, JSONParser])
@permission_classes([InventoryHandle])
def edit_item_inventory(request):
    data = request.data
    try:
        serializer = EditInventorySr(data=data)
        if serializer.is_valid():
            item = InventoryItem.objects.get(id=serializer.validated_data.get('id'))
            item.is_available = serializer.validated_data.get('is_available')
            item.pause_time = serializer.validated_data.get('pause_time')

            item.save()

        return Response({
            "status": status.HTTP_200_OK,
            "message": "Successfully Updated"
        })

    except Exception as e:
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": str(e)
        })


class OutletProductFilter(filters.FilterSet):
    id = filters.CharFilter(field_name="inventory_menu__inventory__outlet__id", lookup_expr='iexact')
    outlet_name = filters.CharFilter(field_name="inventory_menu__inventory__outlet__name", lookup_expr='iexact')

    class Meta:
        model = InventoryItem
        fields = ['id', 'outlet_name']


class OutletItem(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]
    serializer_class = GetOutletProduct
    queryset = InventoryItem.objects.all()
    filterset_class = OutletProductFilter


@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsOwner])
@parser_classes([MultiPartParser, JSONParser])
def remove_other_brand(request):
    data = request.data
    user = request.user
    try:
        benificiary = Owner.objects.filter(user=user).first()
        brand = Brand.objects.filter(subdomain=data["subdomain"]).first()

        if brand.brand_beneficiary.all().filter(user=request.user).exists():
            brand.brand_beneficiary.remove(benificiary)
            brand.save()

            return Response({
                "status": status.HTTP_200_OK,
                "message": "Success fully removed brand"
            })
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"msg": "You are not benificiary of this brand"})

    except Exception as e:
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": str(e)
        })


class BrandBySubdomain(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializerSubdomain
    parser_classes = [JSONParser, MultiPartParser]
    permission_classes = [AllowAny]
    lookup_field = 'subdomain'
