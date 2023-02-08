from django.contrib import admin

from .models import *


@admin.register(OrdersHistory)
class OrderHistoryModelAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'outlet', 'total', 'order_date_time', 'rating', 'status')

@admin.register(Order)
class OrderHistoryModelAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'order_type', 'total', 'outlet', 'payment_method')

admin.site.register(OrderItem)
admin.site.register(DeliveryOrder)
admin.site.register(PickupOrder)
admin.site.register(DineInOrder)
admin.site.register(OrderTracker)
admin.site.register(Notification)