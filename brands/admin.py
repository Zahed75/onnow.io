from django.contrib import admin

from .models import (
    Brand, Outlet, Menu, Item, 
    Inventory, OpeningHoursOnDay
)

from .models import *



@admin.register(Brand)
class BrandModelAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'subdomain', '__owner__')


@admin.register(Outlet)
class OutletModelAdmin(admin.ModelAdmin):
    list_display = ('id','name', '__brand__', 'outlet_owner', '__brand_owner__', 'is_paused', 'is_approved')


@admin.register(Menu)
class MenuModelAdmin(admin.ModelAdmin):
    list_display = ('id','name', '__brand__')


@admin.register(Item)
class ItemModelAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'price')


@admin.register(Inventory)
class InventoryModelAdmin(admin.ModelAdmin):
    list_display = ('__brand__', '__str__')

@admin.register(InventoryMenu)
class InventoryMenuModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'menu')

@admin.register(InventoryItem)
class InventoryItemModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'item')


@admin.register(OpeningHoursOnDay)
class OpeningHoursModelAdmin(admin.ModelAdmin):
    list_display = ('outlet', 'week_day', 'opening_from', 'opening_to', 'active_status')

