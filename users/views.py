import base64
from datetime import datetime

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.contrib.sites.shortcuts import get_current_site
from django.core.files.base import ContentFile
from django.forms import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, ListView, TemplateView
from drf_yasg.utils import swagger_auto_schema
from requests import request
from rest_framework import generics, status, viewsets
from rest_framework.decorators import (api_view, parser_classes,
                                       permission_classes)
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from rest_framework_simplejwt.views import TokenObtainPairView
from uritemplate import partial

from utils.custom_mixin import GetSerializerClassMixin
from utils.custom_permission import IsCustomer
from utils.utils import (create_user_profile, send_invitation_link,
                         send_otp_sms, send_otp_via_mail,
                         send_profile_creation_notification_email)

from .models import Otp, Owner, TemporaryEmail
from .serializers import *

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegistrationDataSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data
            serializer = RegistrationDataSerializer(data=data)
            if serializer.is_valid():
                email = serializer.data.get('email')
                name = serializer.data.get('name')
                phone_number = serializer.data.get('phone_number')
                user_type = serializer.data.get('user_type')
                password = data['password']
                print(password)
                user = User.objects.create_user(email=email, name=name, phone_number=phone_number,
                                                user_type=user_type, password=password)
                send_otp_via_mail(serializer.data.get('email'))

                return Response({
                    'message': 'Success! Please check your email!',
                    'data': serializer.data,
                }, status=status.HTTP_201_CREATED)


            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'message': str(e)
                }
            )


class CustomerRegisterView(generics.CreateAPIView):
    serializer_class = CustomerRegistrationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data
            serializer = CustomerRegistrationSerializer(data=data)
            if serializer.is_valid():
                name = serializer.data.get('name')
                phone_number = serializer.data.get('phone_number')
                user_type = serializer.data.get('user_type')
                password = data['password']
                user = User.objects.create_user(name=name, phone_number=phone_number,
                                                user_type=user_type, password=password)
                response = send_otp_sms(serializer.data.get('phone_number'))
                response = response.json()
                if response["error"] == 0:
                    return Response(data={"data": serializer.data,
                                          "message": "otp send in phone number"},
                                    status=status.HTTP_201_CREATED)

                else:
                    return Response(data={"data": serializer.data,
                                          "message": "problem in sending otp"},
                                    status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'message': str(e)
                }
            )


class VerifyEmail(generics.GenericAPIView):
    serializer_class = OtpVerificationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data
            serializer = OtpVerificationSerializer(data=data)
            if serializer.is_valid():
                email = serializer.data.get('email')
                otp = serializer.data.get('otp')
                otp_objs = Otp.objects.filter(user__email=email, otp=otp, has_used=False,
                                              create_at__gte=(timezone.now() - timezone.timedelta(minutes=1)))
                if not otp_objs.exists():
                    return Response(
                        status=status.HTTP_400_BAD_REQUEST,
                        data={"message": 'Wrong OTP for this email or OTP time expired'}
                    )

                otp_obj = otp_objs.first()
                user = otp_obj.user
                user.is_active = True
                user.verified = True
                otp_obj.has_used = True
                create_user_profile(user)
                user.save()
                otp_obj.save()

                return Response(
                    status=status.HTTP_200_OK,
                    data={'message': 'Verified successfully'}
                )

        except:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'message': 'Something went wrong',
                    'data': serializer.errors
                })


class VerifyPhone(generics.GenericAPIView):
    serializer_class = PhoneOtpVerificationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data
            serializer = PhoneOtpVerificationSerializer(data=data)
            if serializer.is_valid():
                phone = serializer.data.get('phone')
                otp = serializer.data.get('otp')
                otp_objs = Otp.objects.filter(user__phone_number=phone, otp=otp, has_used=False,
                                              create_at__gte=(timezone.now() - timezone.timedelta(minutes=1)))
                if not otp_objs.exists():
                    return Response(
                        status=status.HTTP_400_BAD_REQUEST,
                        data={"message": 'Wrong OTP for this email or OTP time expired'}
                    )

                otp_obj = otp_objs.first()
                user = otp_obj.user
                user.is_active = True
                user.verified = True
                otp_obj.has_used = True
                create_user_profile(user)
                user.save()
                otp_obj.save()

                return Response(
                    status=status.HTTP_200_OK,
                    data={'message': 'Verified successfully'}
                )

            else:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={
                        'message': 'Something went wrong',
                        'data': serializer.errors
                    })

        except:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'message': 'Something went wrong',
                })


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    serializer = ForgotPasswordSerializer(data=request.data)
    if serializer.is_valid():
        try:
            email = serializer.validated_data.get('email')
            user = User.objects.get(email=email)
            send_otp_via_mail.delay(email)
            return Response(
                status=status.HTTP_200_OK,
                data={"message": "OTP send in mail, please check mail"}
            )
        except:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "No user found with email"}
            )
    return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data={
            "message": serializer.errors
        }
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_phone_otp(request):
    serializer = ResendPhoneOtpSerializer(data=request.data)
    if serializer.is_valid():
        try:
            response = send_otp_sms(serializer.data.get('phone'))
            response = response.json()
            if response["error"] == 0:
                return Response(data={
                    "message": "otp send in phone number"},
                    status=status.HTTP_200_OK)

            else:
                return Response(data={"data": serializer.data,
                                      "message": "problem in sending otp"},
                                status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "No user found with this phone"}
            )
    return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data={
            "message": serializer.errors
        }
    )


class TokenVerify(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegistrationDataSerializer

    def post(self, request):
        try:
            payload = request.data
            verify = UntypedToken(token=payload.get('access_token'))

            return Response(
                status=status.HTTP_200_OK,
                data={
                    'access_token': str(verify.token),
                    'token_type': str(verify.payload['token_type']),
                    'expiry': verify.payload['exp'],
                    'user_id': verify.payload['user_id'],
                })
        except Exception as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": str(e)
                })


class OnnowTokenObtainPairView(TokenObtainPairView):
    serializer_class = OnnowTokenObtainPairSerializer
    print(serializer_class.data)
    permission_classes = [AllowAny]


class TokenRefresh(generics.GenericAPIView):
    serializer_class = RegistrationDataSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            payload = request.data
            refresh = RefreshToken(token=payload.get('refresh_token'), verify=True)

            return Response(
                status=status.HTTP_200_OK,
                data={
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                    'token_type': str(refresh.payload['token_type']),
                    'expiry': refresh.payload['exp'],
                    'user_id': refresh.payload['user_id']
                })
        except Exception as e:
            return Response(
                status=status.HTTP_401_UNAUTHORIZED,
                data={
                    "message": str(e)
                }
            )


class RequestPasswordResetEmail(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        email = request.data.get('email')
        try:
            User.objects.get(email=email)
            send_otp_via_mail.delay(email)
            return Response({'success': 'We have sent you a link to reset your password'}, status=status.HTTP_200_OK)
        except:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={
                    "message": "Email not found"
                }
            )


class CheckForgotPasswordOtp(generics.GenericAPIView):
    serializer_class = OtpVerificationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        serializer = OtpVerificationSerializer(data=data)
        if serializer.is_valid():
            try:
                email = serializer.data.get('email')
                otp = serializer.data.get('otp')
                otp_objs = Otp.objects.filter(user__email=email, otp=otp, has_used=False,
                                              create_at__gte=(timezone.now() - timezone.timedelta(minutes=1)))
                if not otp_objs.exists():
                    return Response(
                        status=status.HTTP_401_UNAUTHORIZED,
                        data={"message": 'Wrong OTP for this email or OTP time expired'}
                    )

                return Response(
                    status=status.HTTP_200_OK,
                    data={
                        "message": "Correct OTP, please enter new password"
                    }
                )

            except:
                return Response(
                    status=status.HTTP_401_UNAUTHORIZED,
                    data={
                        "message": "No user with this email, Please Enter correct email"
                    }
                )

        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data={
                "message": serializer.errors
            }
        )


class CheckCustomerForgotPasswordOtp(generics.GenericAPIView):
    serializer_class = PhoneOtpVerificationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        serializer = PhoneOtpVerificationSerializer(data=data)
        if serializer.is_valid():
            try:
                phone = serializer.data.get('phone')
                otp = serializer.data.get('otp')
                otp_objs = Otp.objects.filter(user__username=phone, otp=otp, has_used=False,
                                              create_at__gte=(timezone.now() - timezone.timedelta(minutes=1)))
                if not otp_objs.exists():
                    return Response(
                        status=status.HTTP_401_UNAUTHORIZED,
                        data={"message": 'Wrong OTP for this Phone Number or OTP time expired'}
                    )

                return Response(
                    status=status.HTTP_200_OK,
                    data={
                        "message": "Correct OTP, please enter new password"
                    }
                )

            except:
                return Response(
                    status=status.HTTP_401_UNAUTHORIZED,
                    data={
                        "message": "No user with this Phone Number, Please Enter correct Phone Number"
                    }
                )

        return Response(
            status=status.HTTP_401_UNAUTHORIZED,
            data={
                "message": serializer.errors
            }
        )


class ResetPassword(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        serializer = PasswordResetSerializer(data=data)
        if serializer.is_valid():
            try:
                email = serializer.data.get('email')
                user = User.objects.get(email=email)
                try:
                    validate_password(serializer.data.get('password'), user)
                except Exception as e:
                    return Response(
                        status=status.HTTP_401_UNAUTHORIZED,
                        data={
                            "message": str(e)
                        }
                    )

                password = make_password(serializer.data.get('password'))
                user.password = password
                user.save()

                return Response(
                    status=status.HTTP_200_OK,
                    data={
                        "message": "Password reset successfully",
                        "email": user.email,
                    }
                )

            except:
                return Response(
                    status=status.HTTP_401_UNAUTHORIZED,
                    data={
                        "message": "No user with this email, Please Enter correct email"
                    }
                )

        return Response(
            status=status.HTTP_401_UNAUTHORIZED,
            data={
                "message": serializer.errors
            }
        )


class ResetCustomerPassword(generics.GenericAPIView):
    serializer_class = CustomerPasswordResetSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        serializer = CustomerPasswordResetSerializer(data=data)
        if serializer.is_valid():
            try:
                phone = serializer.data.get('phone')
                user = User.objects.get(username=phone)
                try:
                    validate_password(serializer.data.get('password'), user)
                except Exception as e:
                    return Response(
                        status=status.HTTP_401_UNAUTHORIZED,
                        data={
                            "message": str(e)
                        }
                    )

                password = make_password(serializer.data.get('password'))
                user.password = password
                user.save()

                return Response(
                    status=status.HTTP_200_OK,
                    data={
                        "message": "Password reset successfully"
                    }
                )

            except:
                return Response(
                    status=status.HTTP_401_UNAUTHORIZED,
                    data={
                        "message": "No user with this phone, Please Enter correct phone number"
                    }
                )

        return Response(
            status=status.HTTP_401_UNAUTHORIZED,
            data={
                "message": serializer.errors
            }
        )


# primary function for updating brand managers
@csrf_exempt
@api_view(('PATCH',))

def update_brand_manager(request, id):
    if request.user.is_authenticated:
        manager_ins = Manager.objects.get(pk=id)
        user_ins = User.objects.get(username=manager_ins.user.username)

        all_brands = list(Brand.objects.all())
        brand_list = []

        for item in request.data['manager_brands']:
            brand_ins = Brand.objects.get(pk=item)
            brand_list.append(brand_ins)
            brand_ins.manager.add(manager_ins)
            print(f"manager added to {item}")

        for item in brand_list:
            all_brands.remove(item)

        for item in all_brands:
            item.manager.remove(manager_ins)
            print(f"manager removed from {item.id}")

        user_ins.name = (request.data['user'])['name']
        user_ins.email = (request.data['user'])['email']
        user_ins.phone_number = (request.data['user'])['phone_number']
        # user_ins.user_type = (request.data['user'])['user_type']

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
                "message": "Brand manager updated successfully!"
            }
        )

    else:
        return Response(
            status=status.HTTP_401_UNAUTHORIZED,
            data={
                "message": "Login first to access recourses!"
            }
        )


@parser_classes([MultiPartParser, JSONParser])
class BrandManagerView(GetSerializerClassMixin, viewsets.ModelViewSet):
    """
    This is for documentation purpose
    """
    serializer_class = BrandManagerProfileSerializer
    permission_classes = [IsAuthenticated]

    serializer_action_classes = {
        'retrieve': BrandManagerProfileSerializer,
        'create': BrandManagerProfileSerializer,
        'update': UpdateBMProfileSerializer,
        'partial_update': UpdateBMProfileSerializer
    }

    def get_queryset(self):
        owner = get_object_or_404(Owner, user=self.request.user)
        brands = Brand.objects.filter(owner=owner).values_list('manager', flat=True)
        return Manager.objects.filter(id__in=brands)
        # print('manager=====', Manager.objects.filter(id__in=brands))

    def get_object(self):
        if self.request.method in ['PATCH', 'DELETE']:
            manager = Manager.objects.get(pk=self.kwargs.get('pk'))
            if manager is not None:
                return manager
            else:
                raise Http404()

        return super().get_object()

    def create(self, request, *args, **kwargs):
        try:

            owner = Owner.objects.get(user=request.user)

            has_brand = Brand.objects.filter(owner=owner).exists()
            if has_brand:
                brand_ids = set(request.data.get('manager_brands'))
                brands = Brand.objects.filter(owner=owner).values_list('id', flat=True)

                is_your_brands = brand_ids.issubset(brands)
                if is_your_brands:
                    serializer = self.get_serializer(data=request.data, context={'request': request})
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

                    # send invitation
                    to_email = serializer.data.get('user').get('email')
                    user = User.objects.get(email=to_email)
                    current_site = get_current_site(request).domain
                    relativeLink = reverse('activate-profile')
                    token = RefreshToken.for_user(user).access_token
                    absolute_url = f'https://{str(current_site)}{str(relativeLink)}?token={str(token)}'
                    url = f'https://app.onnow.io/invite/?email={str(to_email)}'
                    data = {
                        'absurl': absolute_url,
                        'to_email': to_email,
                        'user_type': user.user_type,
                        'name': user.name,
                        'url': url
                    }
                    send_invitation_link.delay(data)

                    return Response({
                        'message': 'Brand manager invited!',
                        'data': serializer.data,
                        'activation_link': absolute_url,
                        'url': url
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'errors': 'Select your brands only!',
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'errors': 'Create a brand first!',
                }, status=status.HTTP_400_BAD_REQUEST)

        except Owner.DoesNotExist:
            return Response({
                'errors': "You do not have access to this API",
            }, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:

            return Response({
                # 'brand_id_error': 'Please select your brands only!',
                'errors': serializer.errors,
                'errors': str(e.args[0]),
            }, status=status.HTTP_400_BAD_REQUEST)


    def update(self, request, *args, **kwargs):
        try:
            manager = self.get_object()
            OWNER = Owner.objects.get(user=request.user)
            if manager is not None:
                can_update = Brand.objects.filter(manager=manager, owner=OWNER).exists()
                # print(can_update)
                # print(aco_brand_id)
                if can_update:
                    brand_ids = set(request.data.get('manager_brands'))
                    brands = Brand.objects.filter(owner=OWNER).values_list('id', flat=True)

                    is_your_brands = brand_ids.issubset(brands)
                    if is_your_brands:

                        serializer = self.get_serializer(instance=manager, data=request.data, partial=True)
                        serializer.is_valid(raise_exception=True)
                        serializer.save()
                        return Response({
                            'message': 'Profile updated!',
                            'data': serializer.data,
                        }, status=status.HTTP_200_OK)
                    else:
                        return Response({
                            'errors': "Please select your brands only!",
                        }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({
                        'errors': "You can not update this manager!",
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'errors': "You don't have access to this manager!",
                }, status=status.HTTP_403_FORBIDDEN)

        except Manager.DoesNotExist:
            return Response({
                'errors': 'Manager not found!',
                # 'errors': 'serializer.errors'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            # print(e.__class__)
            response = {}
            if len(serializer.errors) == 0:
                response['errors'] = str(e.args[0])
            else:
                response['errors'] = serializer.errors
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            manager = self.get_object()
            can_delete = Brand.objects.filter(manager=manager, owner=Owner.objects.get(user=request.user)).exists()
            # print(can_update)
            # print(aco_brand_id)
            if can_delete:
                user = User.objects.get(id=manager.user.id)
                user.delete()
                return Response({
                    'message': 'Brand manager deleted'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'errors': "You don't have access to this manager!",
                }, status=status.HTTP_403_FORBIDDEN)

        except:
            return Response({
                'errors': 'No user found!',
            }, status=status.HTTP_400_BAD_REQUEST)


@parser_classes([MultiPartParser, JSONParser])
class OutletManagerView(GetSerializerClassMixin, viewsets.ModelViewSet):
    """
    This is for documentation purpose
    """
    serializer_class = OutletManagerProfileSerializer
    permission_classes = [IsAuthenticated]

    serializer_action_classes = {
        'list': ListOutletManagerSerializer,
        'retrieve': ListOutletManagerSerializer,
        'create': OutletManagerProfileSerializer,
        'update': UpdateOMProfileSerializer,
        'partial_update': UpdateOMProfileSerializer
    }

    def get_queryset(self):

        if self.request.user.user_type == 'ACO':
            OWNER = Owner.objects.get(user=self.request.user)
            brands = Brand.objects.filter(owner=OWNER)

        else:
            MANAGER = Manager.objects.get(user=self.request.user)
            brands = Brand.objects.filter(manager=MANAGER)

        outlets = Outlet.objects.filter(brand__in=brands)
        outlet_managers = OutletManager.objects.filter(om_outlets__in=outlets).distinct()

        return outlet_managers

    def create(self, request, *args, **kwargs):

        try:
            if request.user.user_type == 'ACO':
                owner = Owner.objects.get(user=request.user)
                outlet_ids = set(request.data.get('om_outlets'))
                outlets = Outlet.objects.filter(outlet_owner=owner).values_list('id', flat=True)
                is_your_outlets = outlet_ids.issubset(outlets)
                if is_your_outlets:
                    serializer = self.get_serializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

                    # send invitation
                    to_email = serializer.data.get('user').get('email')
                    user = User.objects.get(email=to_email)
                    current_site = get_current_site(request).domain
                    relativeLink = reverse('activate-profile')
                    token = RefreshToken.for_user(user).access_token
                    absolute_url = f'https://{str(current_site)}{str(relativeLink)}?token={str(token)}'
                    url = f'https://app.onnow.io/invitation/email={str(to_email)}'

                    data = {
                        'absurl': absolute_url,
                        'to_email': to_email,
                        'user_type': user.user_type,
                        'name': user.name,
                        'url': url
                    }
                    send_invitation_link.delay(data)

                    return Response({
                        'message': 'Outlet manager invited!',
                        'data': serializer.data,
                        'url': url,
                        'activation_link': absolute_url
                    }, status=status.HTTP_201_CREATED)

                else:
                    return Response({
                        'errors': 'Select your outlets only!',
                    }, status=status.HTTP_400_BAD_REQUEST)

            elif request.user.user_type == "MGR":
                print("tst kori manager block", request.user.user_type)
                brand = Brand.objects.get(manager__user=request.user.id)

                owner = brand.owner.id
                print("amara brand test", brand, owner)

                outlet_ids = set(request.data.get('om_outlets'))
                print("amar outlet id khuji", outlet_ids)
                outlets = Outlet.objects.filter(outlet_owner=owner).values_list('id', flat=True)
                print("amar abar khuji outlets", outlets)
                is_your_outlets = outlet_ids.issubset(outlets)
                if is_your_outlets:
                    serializer = self.get_serializer(data=request.data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

                    # send invitation
                    to_email = serializer.data.get('user').get('email')
                    user = User.objects.get(email=to_email)
                    current_site = get_current_site(request).domain
                    relativeLink = reverse('activate-profile')
                    token = RefreshToken.for_user(user).access_token
                    absolute_url = f'https://{str(current_site)}{str(relativeLink)}?token={str(token)}'
                    url = f'https://app.onnow.io/invite/?email={str(to_email)}'

                    data = {
                        'absurl': absolute_url,
                        'to_email': to_email,
                        'user_type': user.user_type,
                        'name': user.name,
                        'url': url,

                    }
                    send_invitation_link.delay(data)

                    return Response({
                        'message': 'Outlet manager invited!',
                        'data': serializer.data,
                        'url': url,
                        'activation_link': absolute_url
                    }, status=status.HTTP_201_CREATED)

                else:
                    return Response({
                        'errors': 'Select your outlets only!',
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'message': "Tor kono permission nai"
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response = {}
            if len(serializer.errors) == 0:
                response['errors'] = str(e.args[0])
            else:
                response['errors'] = serializer.errors

            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):

        try:
            if request.user.user_type == 'ACO':

                outletManager = self.get_object()
                owner = Owner.objects.get(user=request.user)
                outlet_ids = set(request.data.get('om_outlets'))
                outlets = Outlet.objects.filter(outlet_owner=owner).values_list('id', flat=True)
                is_your_outlets = outlet_ids.issubset(outlets)
                if is_your_outlets:
                    serializer = self.get_serializer(instance=outletManager, data=request.data, partial=True)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

                    return Response({
                        'message': 'Profile updated!',
                        'data': serializer.data,
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'errors': 'Select your outlets only!',
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'errors': 'You do not have access to this service!',
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            response = {}
            if len(serializer.errors) == 0:
                response['errors'] = str(e.args[0])
            else:
                response['errors'] = serializer.errors

            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):

        try:
            outletManager = self.get_object()
            user = User.objects.get(id=outletManager.user.id)
            user.delete()
            return Response({
                'message': 'Outlet manager deleted'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'errors': 'No user found',
            }, status=status.HTTP_400_BAD_REQUEST)


class ActivateProfileView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.GET.get('token')

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])
            user.is_active = True
            user.verified = True
            user.save()

            # send brand owner a notification email
            if user.user_type == "MGR":
                owner = user.manager.manager_brands.all().first().owner
                relativeLink = 'api/brand-manager'
            else:
                owner = user.outlet_manager.om_outlets.all().first().brand.owner
                relativeLink = 'api/outlet-manager'

            domain = get_current_site(request).domain
            absolute_url = f'http://{domain}/{relativeLink}/'
            data = {
                'to_email': owner.user.email,
                'owner_name': owner.user.name,
                'user_name': user.name,
                'user_type': user.user_type,
                'absurl': absolute_url
            }

            send_profile_creation_notification_email.delay(data)
            # send_profile_creation_notification_email(data)  # test

            return Response({
                'message': 'Your account is activated! Set new password!',
                'email': user.email,
            }, status=status.HTTP_200_OK)

        except jwt.ExpiredSignatureError as error:
            return Response({
                'message': 'Activation link expired',
                'status': status.HTTP_400_BAD_REQUEST
            })

        except jwt.exceptions.DecodeError as error:
            return Response({
                'errors': 'Invalid token',
            }, status=status.HTTP_400_BAD_REQUEST)


# class SetNewPasswordView(generics.GenericAPIView):
#     serializer_class = PasswordResetSerializer
#     permission_classes = [AllowAny]

#     def post(self, request):
#         data = request.data
#         serializer = self.serializer_class(data=data)
#         if serializer.is_valid():
#             try:
#                 email = serializer.data.get('email')
#                 user = User.objects.filter(email=email).first()

#                 try:
#                     validate_password(serializer.data.get('password'), user)
#                 except Exception as e:
#                     return Response({
#                         "errors": serializer.errors,
#                     }, status=status.HTTP_400_BAD_REQUEST)

#                 password = make_password(serializer.data.get('password'))
#                 user.password = password
#                 user.save()

#                 return Response({
#                     'message': "New password created successfully! Login!",
#                     'email': user.email
#                 }, status=status.HTTP_201_CREATED)

#             except:
#                 return Response({
#                     "errors": "No user with this email, Please Enter correct email",
#                 }, status=status.HTTP_400_BAD_REQUEST)

#         return Response({
#             "error": serializer.errors
#         }, status=status.HTTP_400_BAD_REQUEST)


class UserViewsets(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class EditUserView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get(self, request):
        user = request.user
        # print(user)
        serializer = UserSerializer(instance=user)
        return Response({
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def patch(self, request, **kwargs):
        user_object = User.objects.get(id=kwargs['pk'])
        # print(kwargs['pk'])
        serializer = UserSerializer(user_object, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "data": serializer.data,
                "message": "Profile updated!"
            }, status=status.HTTP_200_OK)
        return Response({
            'message': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


class ChangeEmail(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        email = request.data.get('email')

        try:
            # User.objects.get(email=email)
            TemporaryEmail.objects.create(user=request.user, email=email)
            send_otp_via_mail.delay(email, change_email=True)

            return Response({
                'success': 'We have sent you an OTP. Confirm your email!'
            }, status=status.HTTP_200_OK)

        except:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={
                    "message": serializer.error_messages
                }
            )


class VerifyChangedEmail(generics.GenericAPIView):
    serializer_class = OtpVerificationSerializer

    def post(self, request):
        try:
            data = request.data
            serializer = OtpVerificationSerializer(data=data)
            if serializer.is_valid():
                email = serializer.data.get('email')
                otp = serializer.data.get('otp')
                tempEmailObj = TemporaryEmail.objects.filter(email=email).first()
                otp_objs = Otp.objects.filter(
                    user__temp_user_email__email=email,
                    otp=otp,
                    has_used=False,
                    create_at__gte=(timezone.now() - timezone.timedelta(minutes=1))
                )

                if not otp_objs.exists():
                    return Response(
                        status=status.HTTP_400_BAD_REQUEST,
                        data={"message": 'Wrong OTP for this email or OTP time expired'}
                    )

                otp_obj = otp_objs.first()
                user = otp_obj.user
                user.email = user.username = email
                otp_obj.has_used = True
                tempEmailObj.delete()
                user.save()
                otp_obj.save()

                return Response(
                    status=status.HTTP_200_OK,
                    data={'message': 'Verified successfully'}
                )

        except:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'message': 'Something went wrong',
                    'data': serializer.errors
                })


class Logout(APIView):
    def get(self, request, format=None):
        # simply delete the token to force a login
        request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)


# CTO
class ChangePasswordView(generics.UpdateAPIView):
    """
    An endpoint for changing password.
    """
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Password updated successfully',
                'data': []
            }

            return Response(response)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
