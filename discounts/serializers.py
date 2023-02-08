from rest_framework import serializers
from .models import Discount
from brands.models import Brand


class ListDiscountSerializer(serializers.ModelSerializer):

    class Meta:
        model = Discount
        fields = [
            'id', 'title', 'promo_code', 
            'discount_amount', 'minimum_spend',
            'maximum_spend', 'expiry_date'
        ]


class DiscountSerializer(serializers.ModelSerializer):
    expiry_date = serializers.DateField()

    class Meta:
        model = Discount
        fields = [
            'brand', 'title', 'promo_code',
            'discount_amount', 'minimum_spend',
            'maximum_spend', 'expiry_date'
        ]

    def create(self, validated_data):

        discount_obj = Discount.objects.create(**validated_data)
        return discount_obj

    def update(self, instance, validated_data):
        
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        return instance


class BrandWiseDiscountListSerializer(serializers.ModelSerializer):
    brand_discount = ListDiscountSerializer(many=True)

    class Meta:
        model = Brand
        fields = ['id', 'brand_discount']