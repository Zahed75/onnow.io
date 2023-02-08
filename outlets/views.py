import base64

from django.core.files.base import ContentFile
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django_filters import rest_framework as filters
from rest_framework import generics, mixins, status, views, viewsets
from rest_framework.decorators import (api_view, parser_classes,
                                       permission_classes)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from brands.models import Brand, OpeningHoursOnDay, Outlet
from users.models import Manager, OutletManager, Owner, User
from utils.custom_mixin import GetSerializerClassMixin

from .serializers import (CandidateSerializer, CreateOutletSerializer,
                          GroupedOutletListSerializer,
                          OutletsByDeliveryAddressSerializer, OutletSerializer,
                          UpdateOutletSerializer)


# primary function for updating outlet managers
@csrf_exempt
@api_view(('PATCH',))
def update_outlet_manager(request, id):
    if request.user.is_authenticated:
        manager_ins = OutletManager.objects.get(pk=id)
        user_ins = User.objects.get(username=manager_ins.user.username)

        all_outlets = list(Outlet.objects.all())
        brand_list = []

        for item in request.data['om_outlets']:
            brand_ins = Outlet.objects.get(pk=item)
            brand_list.append(brand_ins)
            brand_ins.outlet_manager.add(manager_ins)
            print(f"manager added to {item}")

        for item in brand_list:
            all_outlets.remove(item)

        for item in all_outlets:
            item.outlet_manager.remove(manager_ins)
            print(f"manager removed from {item.id}")

        user_ins.name = (request.data['user'])['name']
        user_ins.email = (request.data['user'])['email']
        user_ins.phone_number = (request.data['user'])['phone_number']

        user_ins.save()

        if 'img' in request.data:
            image_data = request.data['img']
            format, image_string = image_data.split(';base64,')
            extension = format.split('/')[-1]
            data = ContentFile(base64.b64decode(image_string))
            file_name = "'profile_pic." + extension

            manager_ins.img.save(file_name, data, save=True)
            print("Image changed")

        return Response(
            status=status.HTTP_200_OK,
            data={
                "message": "Outlet manager updated successfully!"
            }
        )

    else:
        return Response(
            status=status.HTTP_401_UNAUTHORIZED,
            data={
                "message": "Login first to access recourses!"
            }
        )


class OutletView(GetSerializerClassMixin, viewsets.ModelViewSet):
    serializer_class = OutletSerializer
    permission_classes = [IsAuthenticated]
    queryset = Outlet.objects.all()

    serializer_action_classes = {
        'list': GroupedOutletListSerializer,
        'retrieve': OutletSerializer,
        'create': CreateOutletSerializer,
        'update': UpdateOutletSerializer,
        'partial_update': UpdateOutletSerializer
    }

    def list(self, request, *args, **kwargs):
        if self.request.user.user_type == 'ACO':
            owner = get_object_or_404(Owner, user=self.request.user)
            brands = Brand.objects.filter(owner=owner)
        elif self.request.user.user_type == 'MGR':
            manager = get_object_or_404(Manager, user=self.request.user)
            brands = Brand.objects.filter(manager=manager)
        else:
            return Response({
                'errosr': 'You do have permission to this service!'
            }, status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(brands, many=True)

        return Response({
            'data': serializer.data
        }, status=status.HTTP_200_OK)



    def retrieve(self, request, *args, **kwargs):
        try:
            # print(request.user.user_type)
            if request.user.user_type == 'ACO':
                owner = Owner.objects.get(user=request.user)
                is_your_brand = Brand.objects.filter(id=kwargs['pk'], owner=owner).exists()
                is_brand_beneficiary = Brand.objects.filter(id=kwargs['pk'], brand_beneficiary=owner).exists()
                if is_your_brand:
                    brand = Brand.objects.get(id=kwargs['pk'])
                    outlets = Outlet.objects.filter(brand=brand)
                elif is_brand_beneficiary:
                    brand = Brand.objects.get(id=kwargs['pk'])
                    outlets = Outlet.objects.filter(brand=brand, outlet_owner=owner)
                else:
                    return Response({
                        'data': []
                    }, status=status.HTTP_200_OK)

            elif request.user.user_type == 'MGR':
                manager = Manager.objects.get(user=request.user)
                brand = Brand.objects.get(id=kwargs['pk'])
                is_your_brand = Brand.objects.filter(id=kwargs['pk'], manager=manager).exists()
                if is_your_brand:
                    outlets = Outlet.objects.filter(brand=brand)
                else:
                    return Response({
                        'errosr': 'You do have permission to this service!'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            elif request.user.user_type == "STF":
                outlets = Outlet.objects.filter(brand=kwargs['pk'], outlet_manager__user=request.user)

            else:
                return Response({
                    'errosr': 'You do have permission to this service!'
                }, status=status.HTTP_401_UNAUTHORIZED)

            serializer = self.get_serializer(outlets, many=True)
            return Response({
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Brand.DoesNotExist:
            return Response({
                'errors': "You do no have access to this service!"
            }, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        try:

            if request.user.user_type == "ACO":
                print("test 163")
                owner = Owner.objects.get(user=request.user)
                brand_id = request.data.get('brand')
                brand = Brand.objects.filter(id=brand_id).first()



                if brand.owner == owner:
                    print("test 169")
                    request.data['outlet_status'] = True
                    request.data['is_approved'] = True
                    request.data['outlet_owner'] = owner.id
                    serializer = self.get_serializer(data=request.data)

                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    return Response({
                        'message': 'Outlet created successfully!',

                    }, status=status.HTTP_201_CREATED)

                else:
                    print("test 185")
                    request.data['outlet_status'] = True
                    request.data['is_approved'] = True
                    request.data['outlet_owner'] = owner.id
                    serializer = self.get_serializer(data=request.data)

                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    return Response({
                        'message': 'Outlet created successfully!',

                    }, status=status.HTTP_201_CREATED)


            elif request.user.user_type == "MGR":
                print("test 182")
                print("amra tesrt kortesi", request.user.id)
                brand_id = request.data.get('brand')
                brand = Brand.objects.filter(id=brand_id).first()
                manager = brand.manager.all().filter(user=request.user).exists()
                owner = brand.owner
                print("amara abar", owner.id, brand, manager)
                request.data['outlet_status'] = True
                request.data['is_approved'] = True
                request.data['outlet_owner'] = owner.id
                request.data['outlet_manager'] = request.user.id
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response({
                    'message': 'Outlet created successfully!',
                    # 'data': serializer.data,
                }, status=status.HTTP_201_CREATED)



        except:
            return Response({
                "msg": "Something is wrong"
            }, status=status.HTTP_400_BAD_REQUEST)



def update(self, request, *args, **kwargs):
    try:
        outlet = self.get_object()
        OWNER = Owner.objects.get(user=request.user)
        can_update = outlet.outlet_owner == OWNER or outlet.brand.owner == OWNER
        if can_update:
            serializer = self.get_serializer(instance=outlet, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                'message': 'Outlet updated!',
                'data': serializer.data,
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'You can not update this outlet!',
            }, status=status.HTTP_401_UNAUTHORIZED)

    except Owner.DoesNotExist:
        return Response({
            'errors': 'You do not have the permission to this service!'
        }, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        return Response({
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


def destroy(self, request, *args, **kwargs):
    try:
        outlet = self.get_object()
        # print(outlet)
        OWNER = Owner.objects.get(user=request.user)
        # print(OWNER)
        can_delete = outlet.outlet_owner == OWNER or outlet.brand.owner == OWNER
        print(can_delete)
        if can_delete:
            outlet.delete()
            return Response({
                'message': 'Outlet deleted!'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'You can not delete this outlet!'
            }, status=status.HTTP_400_BAD_REQUEST)

    except Owner.DoesNotExist:
        return Response({
            'errors': 'You do not have the permission to this service!'
        }, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        return Response({
            'errors': 'Outlet not found!',
            'server_error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


class ApproveOutletView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OutletSerializer

    def post(self, request, *args, **kwargs):

        try:
            # print(kwargs)
            OWNER = Owner.objects.get(user=request.user)
            outlet = Outlet.objects.get(id=kwargs['pk'])
            can_approve = outlet.brand.owner == OWNER

            if can_approve:

                if outlet.is_approved == False:
                    outlet.is_approved = True
                    outlet.save()
                    outlet.get_qr_code()
                    return Response({
                        'data': 'Outlet Approved!'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'errors': 'Outlet already Approved!'
                    }, status=status.HTTP_400_BAD_REQUEST)

            else:
                return Response({
                    'errors': 'You can not approve this outlet!'
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'errors': 'you do not have access to this service!',
                # 'server_error': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)


class GetOutletDetailsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreateOutletSerializer

    def get(self, request, *args, **kwargs):

        try:
            perm_ACO = perm_MGR = False
            outlet = Outlet.objects.get(id=kwargs['pk'])
            if request.user.user_type == 'ACO':
                OWNER = Owner.objects.get(user=request.user)
                perm_ACO = outlet.outlet_owner == OWNER or outlet.brand.owner == OWNER
            elif request.user.user_type == 'MGR':
                MANAGER = Manager.objects.get(user=request.user)
                # perm2 = outlet.brand.manager == MANAGER
                perm_MGR = MANAGER in outlet.brand.manager.all()
            else:
                return Response({
                    'errors': 'You do not have permission to this service!'
                }, status=status.HTTP_400_BAD_REQUEST)
            print(perm_ACO)
            print(perm_MGR)
            if perm_ACO or perm_MGR:
                serializer = self.serializer_class(outlet)

                return Response({
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'errors': 'You do not have permission to this service!'
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'errors': 'Bad request!',
                'server_error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class GetCandidateInfo(generics.GenericAPIView):
    """
    This class is returns the Outlet owner's
    basic information including the previous outlets that
    he took
    """

    permission_classes = [IsAuthenticated]
    serializer_class = CandidateSerializer

    def get(self, requests, *args, **kwargs):

        try:
            outlet = Outlet.objects.get(id=kwargs['pk'])
            address = outlet.delivery_area
            context = {'outlet_id': outlet.id}
            # usr = User.objects.get(id=outlet.outlet_owner.user.id)
            serializer = self.serializer_class(outlet.outlet_owner, context=context)
            # if serializer.is_valid(raise_exception=True):
            return Response({
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            # else:
            #     return Response({
            #     'errors': serializer.errors
            # }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'errors': str(e.args[0])
            }, status=status.HTTP_400_BAD_REQUEST)


class GetOutletsbyDeliveryAddress(views.APIView):
    serializer_class = OutletsByDeliveryAddressSerializer
    permission_classes = [AllowAny]

    def get(self, requests, *args, **kwargs):

        try:
            q_params = self.request.query_params
            brand = Brand.objects.get(id=kwargs['pk'])
            # print(q_params['delivery_area'])
            outlets = Outlet.objects.filter(
                brand=brand,
                delivery_area__icontains=q_params['delivery_area']
            )
            print(outlets)
            serializer = self.serializer_class(outlets, many=True)
            return Response({
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'errors': 'something went wrong!',
                'server_error': e
            }, status=status.HTTP_400_BAD_REQUEST)

        # except Exception as e:
        #     return Response({
        #         'errors': e.args[0]
        #     }, status=status.HTTP_400_BAD_REQUEST)


class OutletFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr='iexact')

    class Meta:
        model = Outlet
        fields = ['name']


class GetOutletbyName(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication]
    serializer_class = OutletsByDeliveryAddressSerializer
    queryset = Outlet.objects.all()
    filterset_class = OutletFilter
