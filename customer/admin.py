from operator import imod
from django.contrib import admin
from .models import  *
# Register your models here.


admin.site.register(Customer)

@admin.register(DeliveryAddress)
class DeliveryAddressModelAdmin(admin.ModelAdmin):
    list_display = ('id','__str__')
