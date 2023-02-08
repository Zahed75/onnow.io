from django.db.models.functions import Cast
from django.db.models.fields import DateField
from django.db.models import Sum

from rest_framework import serializers

from .models import Customer, DeliveryAddress
from orders.models import Order


class CustomerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='customer.user.name')
    phone_number = serializers.CharField(source='customer.user.phone_number')
    no_of_orders = serializers.SerializerMethodField()
    first_order = serializers.SerializerMethodField()
    last_order = serializers.SerializerMethodField()
    total_revenue = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'name', 'phone_number', 'no_of_orders', 
            'first_order', 'last_order', 'total_revenue'
        ]

    def get_no_of_orders(self, obj):
        no_of_orders = Order.objects \
                            .filter(customer=obj.customer, outlet__in=self.context['outlets']) \
                            .count()
        return no_of_orders

    def get_first_order(self, obj):
        create_at = Order.objects \
                            .filter(customer=obj.customer, outlet__in=self.context['outlets']) \
                            .order_by('create_at') \
                            .values('create_at') \
                            .first()
        return create_at['create_at'].date()

    def get_last_order(self, obj):
        create_at = Order.objects \
                            .filter(customer=obj.customer, outlet__in=self.context['outlets']) \
                            .order_by('create_at') \
                            .values('create_at') \
                            .last()
        return create_at['create_at'].date()

    def get_total_revenue(self, obj):
        total = Order.objects \
                        .filter(customer=obj.customer, outlet__in=self.context['outlets']) \
                        .aggregate(Sum('total'))
        return total['total__sum']

    
class AddressSerializer(serializers.ModelSerializer):
    delivery_instruction = serializers.CharField(required=False)
    class Meta:
        model = DeliveryAddress
        fields = ['area','street_address','delivery_instruction','label']


class ReadAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAddress
        fields = '__all__'