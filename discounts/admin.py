from django.contrib import admin
from .models import Discount


@admin.register(Discount)
class DiscountModelAdmin(admin.ModelAdmin):
    list_display = ('title', 'promo_code', 'discount_amount', '__brand__')