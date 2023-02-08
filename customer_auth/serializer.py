from rest_framework import serializers

class ChangeName(serializers.Serializer):
    name = serializers.CharField(max_length=100)

class ChangePassword(serializers.Serializer):
    current_password = serializers.CharField(max_length=20)
    new_password = serializers.CharField(max_length=20)

class ChangePhone(serializers.Serializer):
    phone = serializers.CharField(max_length=20)


class PhoneOtpVerificationSerializer(serializers.Serializer):
    phone = serializers.CharField()
    otp = serializers.CharField()


class ResendPhoneOtpSerializer(serializers.Serializer):
    phone = serializers.CharField()