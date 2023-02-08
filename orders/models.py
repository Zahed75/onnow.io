import datetime

import string
from django.contrib.auth.models import User
import channels.layers
from asgiref.sync import async_to_sync
import json
import random
from channels.layers import get_channel_layer

from django.db import models

from brands.models import BaseModel, Item, Outlet, InventoryItem
from customer.models import DeliveryAddress, Customer
from django.db.models.signals import post_save
from django.dispatch import receiver



class OrdersHistory(BaseModel):
    order_id = models.CharField(max_length=120, unique=True)
    customer_name = models.CharField(max_length=120)
    phone_number = models.CharField(max_length=120)
    outlet = models.CharField(max_length=120)
    payment_method = models.CharField(max_length=120)
    order_type = models.CharField(max_length=120)
    channel = models.CharField(max_length=120)
    total = models.DecimalField(max_digits=6, decimal_places=2)
    order_date_time = models.CharField(max_length=120)
    rating = models.PositiveIntegerField()
    status = models.CharField(max_length=120)

    def __str__(self):
        return f"{self.order_id} - {self.outlet}"


class Order(BaseModel):
    ORDER_TYPE_CHOICES = [
        ('DEV', 'Delivery'),
        ('PIC', 'Pick UP'),
        ('DIN', 'Dine In'),
    ]
    ORDER_STATUS_CHOICES = [
        ('PN', 'PENDING'),
        ('CC', 'Customer Confirmed'),
        ('RC', 'Rider Confirmed'),
        ('WT', 'Waiting'),
        ('DP', 'Dispatched'),
        ('CN', 'Cancelled')
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='order_customer')
    order_id = models.CharField(max_length=20, unique=True)
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='order_outlet')
    sub_total = models.FloatField()
    vat = models.FloatField()
    discount = models.FloatField()
    order_status = models.CharField(choices=ORDER_STATUS_CHOICES, max_length=20)
    total = models.FloatField()
    payment_method = models.CharField(max_length=30)
    order_type = models.CharField(choices=ORDER_TYPE_CHOICES, max_length=20)
    channel = models.CharField(default="Web", max_length=30)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_id}-{self.customer.user.name}"


class OrderTracker(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_tracker')
    title = models.CharField(max_length=100)
    order_status = models.CharField(max_length=2)

    @staticmethod
    def give_order_tracker(order_id):
        instance = list(OrderTracker.objects.filter(order__order_id=order_id).values())
        return instance

class Notification(BaseModel):
    ORDER_STATUS_CHOICES = [
        ('PN', 'PENDING'),
        ('CC', 'Customer Confirmed'),
        ('RC', 'Rider Confirmed'),
        ('WT', 'Waiting'),
        ('DP', 'Dispatched'),
        ('CN', 'Cancelled')
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='notified_customer')
    order_id = models.CharField(max_length=20)
    order_status = models.CharField(choices=ORDER_STATUS_CHOICES, max_length=20)
    title = models.CharField(max_length=300)


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_item')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='single_item')
    quantity = models.PositiveIntegerField(default=0)


class DeliveryOrder(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='delivery')
    delivery_charge = models.PositiveIntegerField()
    delivery_time = models.DateTimeField(null=True,blank=True)
    address = models.ForeignKey(DeliveryAddress, on_delete=models.SET_NULL, related_name='order_delivery_address', null=True)

class PickupOrder(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_pickup')
    pickup_time = models.DateTimeField()

class DineInOrder(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_dine')
    table_number = models.CharField(max_length=40)



@receiver(post_save, sender=OrderItem)
def order_item_count(sender, instance, created, **kwargs):
    if created:
        inventory_item = InventoryItem.objects.filter(inventory_menu__inventory__outlet=instance.order.outlet,
                                                      item=instance.item).first()
        print(inventory_item)
        inventory_item.order_count = inventory_item.order_count + instance.quantity
        print(inventory_item.order_count)
        inventory_item.save()


@receiver(post_save, sender=OrderTracker)
def order_tracker_send(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        data = {}
        data['order_id'] = instance.order.order_id
        data['title'] = instance.title
        data['order_status'] = instance.order_status
        data['create_at'] = str(instance.create_at)
        async_to_sync(channel_layer.group_send)(
            'order_%s' % instance.order.order_id, {
                'type': 'order_status_track',
                'value': json.dumps(data)
            }
        )