from django.db import models
from users.models import BaseModel,User
from brands.models import Brand, Item


class Customer(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_customer')


    def __str__(self):
        return self.user.name

class DeliveryAddress(BaseModel):
    customer = models.ForeignKey(Customer,on_delete=models.CASCADE, related_name='delivery_address')
    area = models.CharField(max_length=200)
    street_address = models.CharField(max_length=200)
    delivery_instruction = models.CharField(max_length=500, null=True, blank=True)
    label = models.CharField(max_length=40)

    def __str__(self):
        return self.street_address + self.area
