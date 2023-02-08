from datetime import datetime

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import time
from django.utils import timezone


class BaseModel(models.Model):
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CustomUserManager(BaseUserManager):

    def create_superuser(self, username, password, **other_fields):

        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_superuser', True)
        other_fields.setdefault('is_active', True)

        if other_fields.get('is_staff') is not True:
            raise ValueError('Superuser must be assigned to is_staff=True.')
        if other_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must be assigned to is_superuser=True.')

        superuser = self.model(username=username, **other_fields)
        superuser.set_password(password)
        superuser.save()
        return superuser

    def create_user(self, phone_number, user_type, name, password, email=None):
        if user_type == "CUS":
            user = self.model(username=phone_number, phone_number=phone_number,
                              user_type=user_type,
                              email=email,
                              name=name
                              )

        else:
            if not email:
                raise ValueError('You must provide an email address')

            email = self.normalize_email(email)
            user = self.model(email=email, username=email, name=name, phone_number=phone_number,
                              user_type=user_type)
        user.set_password(password)
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    USER_TYPE_CHOICES = [
        ('ACO', 'AC_Owner'),
        ('MGR', 'Manager'),
        ('STF', 'Outlet_Manager'),
        ('CUS', 'Customer')
    ]

    username = models.CharField(max_length=225, unique=True)
    email = models.EmailField(unique=True, null=True)
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, unique=True, null=True)
    user_type = models.CharField(choices=USER_TYPE_CHOICES, max_length=20, default='', blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'

    def __str__(self):
        if self.is_staff == True:
            return f"{self.username}"

        return f"{self.name} - {self.user_type}"


class Owner(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, related_name='owner')

    def __str__(self):
        return f"{self.user.name}"


class Manager(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, related_name='manager')
    img = models.ImageField(upload_to='Manager_photos', blank=True, default='')

    def __str__(self):
        return f"{self.user.name} - {self.user.user_type}"


class OutletManager(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='outlet_manager', null=True)
    img = models.ImageField(upload_to='OutletHub', blank=True, default='')

    def __str__(self):
        return f"{self.user.name} - {self.user.user_type}"


class Otp(BaseModel):
    user = models.ForeignKey(User, related_name='otp_user', on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    has_used = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.otp}-{self.user.name}"


class TemporaryEmail(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='temp_user_email')
    email = models.EmailField(blank=True)


    

    # def __str__(self) -> str:
    #     return f"{self.email}-{self.user.name}"

# def create_user_post_save(sender,instance, created, *args, **kwargs):
#     if created:
#         user = InventoryMenu.objects.filter(menu=instance.menu)
#         m_list = []
#         for i in menus:
#             m_list.append(InventoryItem(inventory_menu=i,item=instance))
#         objs = InventoryItem.objects.bulk_create(m_list)
#
# post_save.connect(create_outlet_post_save, sender=Outlet)
