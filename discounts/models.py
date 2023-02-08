from django.db import models
from users.models import BaseModel
from brands.models import Brand


class Discount(BaseModel):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='brand_discount')
    title = models.CharField(max_length=255)
    promo_code = models.CharField(max_length=100, unique=True)
    discount_amount = models.FloatField(default=0)
    minimum_spend = models.FloatField(default=0)
    maximum_spend = models.FloatField(default=0)
    expiry_date = models.DateField()

    def __str__(self):
        return f"{self.title}-{self.promo_code}"

    def __brand__(self):
        """
        This function returens the brand name that a menu is associated with.
        Purpose: Admin Panel Convenience.
        """
        return self.brand.name