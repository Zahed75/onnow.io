from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import models
from django.db.models.base import Model
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from brands.models import Brand, Outlet
from users.models import Manager, OutletManager, Owner

User = get_user_model()


class RegistrationDataSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=256, write_only=True)
    phone_number = serializers.RegexField("^\+8801|8801|01|008801[1|3-9]{1}(\d){8}$")

    class Meta:
        model = User
        fields = ['email', 'name', 'phone_number', 'password', 'user_type']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    # def create(self, validated_data):
    #     return User.objects.create_user(**validated_data)


class CustomerRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=256, write_only=True)
    phone_number = serializers.RegexField("^(?:\+?88|0088)?01[13-9]\d{8}$")

    class Meta:
        model = User
        fields = ['name', 'phone_number', 'password', 'user_type']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    # def create(self, validated_data):
    #     return User.objects.create_user(**validated_data)


class OtpVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()


class PhoneOtpVerificationSerializer(serializers.Serializer):
    phone = serializers.CharField()
    otp = serializers.CharField()


class OnnowTokenObtainPairSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        "no_active_account": "username or password is incorrect!",
    }

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        data['expiry_data'] = str(refresh.payload['exp'])
        data['user_id'] = str(refresh.payload['user_id'])

        # Add extra responses here
        data['username'] = self.user.username
        data['user_type'] = self.user.user_type
        # data['groups'] = self.user.groups.values_list('name', flat=True)
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    class Meta:
        fields = ['email']


class ResendPhoneOtpSerializer(serializers.Serializer):
    phone = serializers.CharField()


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class CustomerPasswordResetSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    # user_type = serializers.CharField(source="user.user_type", write_only=True)
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'phone_number', 'user_type')

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.email = validated_data.get('email', instance.email)
        instance.username = instance.email
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.user_type = validated_data.get('user_type', instance.user_type)
        instance.save()
        return instance


class BrandManagerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    img = Base64ImageField(required=False)

    class Meta:
        model = Manager
        fields = ('id', 'user', 'img', 'manager_brands')

    def create(self, validated_data):
        user = validated_data.pop('user')
        user['username'] = user['email']
        user['is_active'] = True  # test case

        brands = validated_data.pop('manager_brands')

        img = validated_data.get('img')
        user_obj = UserSerializer.create(UserSerializer(), validated_data=user)
        manager_obj = Manager.objects.create(user=user_obj, img=img)
        manager_obj.manager_brands.set(brands)
        manager_obj.save()

        return manager_obj


class UpdateBMProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    img = Base64ImageField(required=False)

    class Meta:
        model = Manager
        fields = ('id', 'user', 'img', 'manager_brands')

    def update(self, instance, validated_data):
        user_data = validated_data.get('user')
        brands = validated_data.get('manager_brands')
        if user_data is not None:
            user_obj = User.objects.get(id=instance.user.id)
            user = UserSerializer.update(self, instance=user_obj, validated_data=user_data)
            instance.user = user
        instance.img = validated_data.get('img', instance.img)
        instance.manager_brands.set(brands)
        instance.save()

        return instance

class GroupedOutletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Outlet
        fields = ['id', 'brand']


class ListOutletManagerSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    img = Base64ImageField(required=False)
    om_outlets = GroupedOutletSerializer(many=True)

    class Meta:
        model = OutletManager
        fields = ('id', 'user', 'img', 'om_outlets')


class OutletManagerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    img = Base64ImageField(required=False)

    class Meta:
        model = OutletManager
        fields = ('id', 'user', 'img', 'om_outlets')

    def create(self, validated_data):
        user = validated_data.pop('user')
        user['username'] = user['email']
        outlets = validated_data.pop('om_outlets')

        img = validated_data.get('img')
        user_obj = UserSerializer.create(UserSerializer(), validated_data=user)
        outletManager_obj = OutletManager.objects.create(user=user_obj, img=img)

        outletManager_obj.om_outlets.set(outlets)
        outletManager_obj.save()

        return outletManager_obj


class UpdateOMProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    img = Base64ImageField(required=False)

    class Meta:
        model = OutletManager
        fields = ('id', 'user', 'img', 'om_outlets')

    def update(self, instance, validated_data):
        user_data = validated_data.get('user')
        outlets = validated_data.get('om_outlets')

        if user_data is not None:
            user_obj = User.objects.get(id=instance.user.id)
            user = UserSerializer.update(self, instance=user_obj, validated_data=user_data)
            instance.user = user

        instance.img = validated_data.get('img', instance.img)
        instance.om_outlets.set(outlets)

        instance.save()

        return instance


# Password Change serializer

from django.contrib.auth.models import User
from rest_framework import serializers


class ChangePasswordSerializer(serializers.Serializer):
    model = User

    """
    Serializer for password change endpoint.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
