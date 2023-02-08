from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.decorators import permission_classes, api_view, authentication_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from utils.utils import send_otp_sms, send_phone_edit_otp_sms
from .models import EditPhoneOtp

User = get_user_model()
from utils.custom_permission import IsCustomer

from .serializer import *


@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsCustomer])
def change_name(request):
    try:
        serializer = ChangeName(data=request.data)
        if serializer.is_valid():
            user = request.user
            user.name = serializer.data.get('name')
            user.save()

            return Response(
                status=status.HTTP_200_OK,
                data={
                    "message": "Name Updated Successfully"
                }
            )
    except Exception as e:
        return Response(
            status=status.HTTP_401_UNAUTHORIZED,
            data={
                "message": str(e)
            }
        )


@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsCustomer])
def change_password(request):
    try:
        serializer = ChangePassword(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.data.get('current_password')):
                raise ValidationError('Invalid current password')

            password = make_password(serializer.data.get('new_password'))
            user.password = password
            user.save()

            return Response(
                status=status.HTTP_200_OK,
                data={
                    "message": "Password updated successfully"
                }
            )
    except Exception as e:
        return Response(
            status=status.HTTP_401_UNAUTHORIZED,
            data={
                "message": str(e)
            }
        )


@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsCustomer])
def change_phone(request):
    try:
        serializer = ChangePhone(data=request.data)
        if serializer.is_valid():
            user = request.user
            response = send_phone_edit_otp_sms(serializer.data.get('phone'))
            response = response.json()
            if response["error"] == 0:
                return Response(data={"data": serializer.data,
                                      "message": "otp send in phone number"},
                                status=status.HTTP_201_CREATED)

            else:
                return Response(data={"data": serializer.data,
                                      "message": "problem in sending otp"},
                                status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response(
            status=status.HTTP_401_UNAUTHORIZED,
            data={
                "message": str(e)
            }
        )


class editPhone_OTP(generics.GenericAPIView):
    serializer_class = PhoneOtpVerificationSerializer
    permission_classes = [IsCustomer]

    def post(self, request):
        try:
            data = request.data
            serializer = PhoneOtpVerificationSerializer(data=data)
            if serializer.is_valid():
                phone = serializer.data.get('phone')
                otp = serializer.data.get('otp')
                otp_objs = EditPhoneOtp.objects.filter(phone=phone, otp=otp, has_used=False,
                                              create_at__gte=(timezone.now() - timezone.timedelta(minutes=1)))
                if not otp_objs.exists():
                    return Response(
                        status=status.HTTP_400_BAD_REQUEST,
                        data={"message": 'Wrong OTP for this Phone or OTP time expired'}
                    )

                user = request.user
                user.username = phone
                user.phone_number = phone
                user.save()

                return Response(
                    status=status.HTTP_200_OK,
                    data={'message': 'Updated Phone Number successfully'}
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
@permission_classes([IsCustomer])
def resend_phone_otp(request):
    serializer = ResendPhoneOtpSerializer(data=request.data)
    if serializer.is_valid():
        try:
            response = send_phone_edit_otp_sms(serializer.data.get('phone'))
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
                data={"message": "Error in serializer"}
            )
    return Response(
        status=status.HTTP_400_BAD_REQUEST,
        data={
            "message": serializer.errors
        }
    )