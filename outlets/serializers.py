from rest_framework import serializers
from brands.models import (
    Brand, Outlet, OpeningHoursOnDay, 
    PAYMENT_TYPE_CHOICE, Inventory
)
from users.serializers import User, Owner, UserSerializer


class OutletListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Outlet
        fields = ['id', 'name']


class OpeningHourSerializer(serializers.ModelSerializer):
    opening_from = serializers.TimeField()
    opening_to = serializers.TimeField()

    class Meta:
        model = OpeningHoursOnDay
        fields = ['id', 'opening_from', 'opening_to', 'week_day', 'active_status']


class OutletSerializer(serializers.ModelSerializer):

    class Meta:
        model = Outlet
        fields = [
            'id', 'name', 'is_approved', 
            'delivery_area', 'qr_code'
        ]


class GroupedOutletListSerializer(serializers.ModelSerializer):
    outlet_brands = OutletListSerializer(many=True)

    class Meta:
        model = Brand
        fields = ['id', 'name', 'logo_img', 'outlet_brands']
        
    
class CreateOutletSerializer(serializers.ModelSerializer):
    outlet_oh = OpeningHourSerializer(many=True)
    payment_methods = serializers.MultipleChoiceField(choices=PAYMENT_TYPE_CHOICE)

    class Meta:
        model = Outlet
        fields = [
            'id', 'brand', 'name', 'outlet_owner', 'address', 'phone_number', 'delivery_charge',
            'delivery_time', 'tax_rate', 'outlet_status', 'qr_code', 'is_approved',
            'tax_type', 'payment_methods',
            'delivery_area', 'table_numbers',
            'outlet_oh'
        ]

    def create(self, validated_data):
        
        opening_hours = validated_data.pop('outlet_oh')
        outlet_obj = Outlet.objects.create(**validated_data)

        if 'outlet_status' in validated_data:
            if validated_data['outlet_status']:
                outlet_obj.get_qr_code()

        for opening_hour in opening_hours:
            opening_hour['outlet'] = outlet_obj
            OpeningHourSerializer.create(OpeningHourSerializer(), validated_data=opening_hour)

        return outlet_obj


class UpdateOutletSerializer(serializers.ModelSerializer):
    outlet_oh = OpeningHourSerializer(many=True)
    payment_methods = serializers.MultipleChoiceField(choices=PAYMENT_TYPE_CHOICE)

    class Meta:
        model = Outlet
        fields = [
            'brand', 'name', 'address', 'phone_number', 'delivery_charge',
            'delivery_time', 'tax_rate', 'qr_code',
            'tax_type', 'payment_methods',
            'delivery_area', 'table_numbers',
            'outlet_oh'
        ]

    def update(self, instance, validated_data):
        
        opening_hours = validated_data.pop('outlet_oh')
        if opening_hours is not None:
            for opening_hour in opening_hours:
                opening_hr_obj = OpeningHoursOnDay.objects.get(outlet=instance, week_day=opening_hour['week_day'])
                opening_hour['outlet'] = instance
                OpeningHourSerializer.update(self, instance=opening_hr_obj, validated_data=opening_hour)
            # print(opening_hr_obj)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        return instance


class TakenOutletsBrandSerializer(serializers.ModelSerializer):

    class Meta:
        model = Brand
        # fields = 


class TakenOutletSerializer(serializers.ModelSerializer):
    brand = serializers.CharField(source='brand.name')
    brand_logo = serializers.ImageField(source='brand.logo_img')
    class Meta:
        model = Outlet
        fields = ['name', 'brand', 'brand_logo', 'is_approved']

class CandidateSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    taken_outlets = TakenOutletSerializer(many=True)
    address = serializers.SerializerMethodField()

    class Meta:
        model = Owner
        fields = ['user', 'address','taken_outlets']

    def get_address(self, obj):
        print(self.context['outlet_id'])
        outlet = Outlet.objects.get(id=self.context['outlet_id'])
        return outlet.delivery_area


class OutletsByDeliveryAddressSerializer(serializers.ModelSerializer):
    outlet_oh = OpeningHourSerializer(many=True)
    payment_methods = serializers.MultipleChoiceField(choices=PAYMENT_TYPE_CHOICE)
    paused = serializers.SerializerMethodField()

    class Meta:
        model = Outlet
        fields = [
            'id', 'brand', 'name', 'outlet_owner', 'address', 'phone_number', 'delivery_charge',
            'delivery_time', 'tax_rate', 'outlet_status', 'qr_code', 'is_approved',
            'tax_type', 'payment_methods',
            'delivery_area', 'table_numbers',
            'paused',
            'outlet_oh'
        ]

    def get_paused(self, obj):
        pause_info = Inventory.objects.get(outlet=obj)
        return {
            'is_available': pause_info.is_available,
            'pause_time': pause_info.pause_time
        }
