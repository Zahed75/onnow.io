import random

from rest_framework import serializers

from .models import *


class OrderItemSr(serializers.ModelSerializer):
    item_name = serializers.ReadOnlyField(source='item.name')
    price = serializers.ReadOnlyField(source='item.price')

    class Meta:
        model = OrderItem
        fields = ['item_name', 'price', 'quantity']


class DeliverySr(serializers.ModelSerializer):
    delivery_area = serializers.ReadOnlyField(source='address.area')
    street_address = serializers.ReadOnlyField(source='address.street_address')

    class Meta:
        model = DeliveryOrder
        fields = ['delivery_charge', 'delivery_time', 'delivery_area', 'street_address']


class DineInSr(serializers.ModelSerializer):
    class Meta:
        model = DineInOrder
        fields = ['table_number']


class PickUpSr(serializers.ModelSerializer):
    class Meta:
        model = PickupOrder
        fields = '__all__'


class ReadLiveOrderSr(serializers.ModelSerializer):
    brand = serializers.ReadOnlyField(source='outlet.brand.name')
    outlet = serializers.ReadOnlyField(source='outlet.name')
    customer_name = serializers.ReadOnlyField(source='customer.user.name')
    customer_phone = serializers.ReadOnlyField(source='customer.user.phone_number')
    delivery = DeliverySr(many=True, required=False)
    order_pickup = PickUpSr(many=True, required=False)
    order_dine = DineInSr(many=True, required=False)
    order_item = OrderItemSr(many=True)
    order_type = serializers.ChoiceField(choices=Order.ORDER_TYPE_CHOICES)

    class Meta:
        model = Order
        fields = ['id','brand','outlet',
                  'customer_name','customer_phone','order_id','create_at', 'sub_total','vat','discount','order_status',
                  'total','payment_method','order_type','delivery','order_item','order_pickup', 'order_dine',
                  'channel']


class ReadOrderHistorySr(serializers.ModelSerializer):
    outlet = serializers.ReadOnlyField(source='outlet.name')
    customer_name = serializers.ReadOnlyField(source='customer.user.name')
    customer_phone = serializers.ReadOnlyField(source='customer.user.phone_number')
    class Meta:
        model = Order
        fields = ['order_id','outlet',
                  'customer_name','customer_phone',
                  'payment_method','order_type','channel',
                  'total',
                  'create_at',
                  'order_status',
                  ]


class CreateOrderDeliverySr(serializers.ModelSerializer):
    delivery_time = serializers.DateTimeField(required=False)
    class Meta:
        model = DeliveryOrder
        fields = ['delivery_charge','delivery_time','address']


class CreateOrderPickupSr(serializers.ModelSerializer):
    pickup_time = serializers.DateTimeField(required=False)
    class Meta:
        model = PickupOrder
        fields = ['pickup_time']

class CreateOrderDineInSr(serializers.ModelSerializer):
    class Meta:
        model = DineInOrder
        fields = ['table_number']


class CreateOrderItemSr(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["item",'quantity']


def generate_orderId():
    id = random.randint(10000000, 99999999)
    order_id = 'O' + str(id)
    try:
        order = Order.objects.get(order_id=order_id)
        generate_orderId()
    except:
        return order_id


class CustomerPlaceOrder(serializers.ModelSerializer):
    delivery = CreateOrderDeliverySr(many=True, required=False)
    order_pickup = CreateOrderPickupSr(many=True, required=False)
    order_dine = CreateOrderDineInSr(many=True, required=False)
    order_item = CreateOrderItemSr(many=True)

    class Meta:
        model = Order
        fields = ['outlet', 'sub_total', 'vat', 'discount', 'order_status',
                  'total', 'payment_method', 'order_type',
                  'delivery',
                  'order_item',
                  'order_dine',
                  'order_pickup',
                  'channel']

    def create(self, validated_data):
        delivery_datas =None
        pickup_datas = None
        dinein_datas = None
        if validated_data.__contains__('delivery'):
            delivery_datas = validated_data.pop('delivery')

        elif validated_data.__contains__('order_pickup'):
            pickup_datas = validated_data.pop('order_pickup')

        elif validated_data.__contains__('order_dine'):
            dinein_datas = validated_data.pop('order_dine')
        order_item = validated_data.pop('order_item')
        order = Order.objects.create(customer=self.context['request'].user.user_customer,
                                     order_id=generate_orderId(),
                                     **validated_data)

        for item in order_item:
            OrderItem.objects.create(order=order, **item)
        if delivery_datas is not None:
            for delivery_data in delivery_datas:
                DeliveryOrder.objects.create(order=order, **delivery_data)

        elif pickup_datas is not None:
            for pickup_data in pickup_datas:
                PickupOrder.objects.create(order=order, **pickup_data)

        elif dinein_datas is not None:
            for dinein_data in dinein_datas:
                DineInOrder.objects.create(order=order, **dinein_data)
        return order


class CustomerOrderListSr(serializers.ModelSerializer):
    order_item = OrderItemSr(many=True)

    class Meta:
        model = Order
        fields = ['order_id',
                  'order_item','create_at']


class OrderTrackerSr(serializers.ModelSerializer):
    class Meta:
        model = OrderTracker
        fields = ['title','create_at', 'order_status']


# class OrderTrackerSrSocket(serializers.ModelSerializer):
#     class Meta:
#         model = OrderTracker
#         fields = ['title','create_at']


class CustomerOrderDetailsSr(serializers.ModelSerializer):
    delivery = DeliverySr(many=True)
    order_item = OrderItemSr(many=True)
    order_tracker = OrderTrackerSr(many=True)

    class Meta:
        model = Order
        fields = ['outlet', 'sub_total', 'vat', 'discount', 'order_status',
                  'total', 'payment_method', 'order_type',
                  'delivery',
                  'order_item',
                  'order_tracker']


class orderTrcker(serializers.ModelSerializer):
    class Meta:
        model = OrderTracker
        fields = '__all__'


class EditLiveOrder(serializers.Serializer):
    order_status = serializers.CharField()
    title = serializers.CharField()


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'