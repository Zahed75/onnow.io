from django.db import models

from users.models import BaseModel


# Create your models here.

class EditPhoneOtp(BaseModel):
    phone = models.CharField(max_length=20)
    otp = models.CharField(max_length=6)
    has_used = models.BooleanField(default=False)