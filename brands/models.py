from django.db import models
from django.db.models.signals import post_save
from django.contrib.postgres.fields import ArrayField
from multiselectfield import MultiSelectField

from users.models import BaseModel, Owner, Manager, OutletManager

# dependencies to .get_qr_code()
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image, ImageDraw

TAX_TYPE_CHOICE = [
        ('IN', 'inclusive'),
        ('EX', 'exclusive')
    ]

PAYMENT_TYPE_CHOICE = [
    ('Cash on Delivery', 'Cash on Delivery'),
    ('Digital Payment', 'Digital Payment')
]


class Brand(BaseModel):
    owner = models.ForeignKey(Owner, on_delete=models.SET_NULL, null=True, related_name='owner')
    manager = models.ManyToManyField(Manager, blank=True, null=True, related_name='manager_brands')
    subdomain = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=255, unique=True)
    brand_color = models.CharField(max_length=10, blank=True)
    text_color = models.CharField(max_length=10, blank=True)
    banner_img = models.ImageField(upload_to='brands/banner', blank=True, null=True)
    logo_img = models.ImageField(upload_to='brands/logo', blank=True, null=True)
    brand_beneficiary = models.ManyToManyField(Owner, related_name='brand_beneficiary', blank=True)

    def __str__(self):
        return self.name

    def __owner__(self):
        """
        This function returens the owner name of a brand.
        Purpose: Admin Panel Convenience.
        """
        try:
            return self.owner.user.name
        except:
            return ""

    @property
    def outlet_number(self):
        return self.outlet_brands.all().count()


class Outlet(BaseModel):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='outlet_brands')
    outlet_manager = models.ManyToManyField(OutletManager, blank=True, related_name='om_outlets')
    outlet_owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='taken_outlets')
    
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, null=True, default='01', blank=True)
    address = models.CharField(max_length=255)
    
    outlet_status = models.BooleanField(default=False, blank=True)
    is_paused = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    qr_code = models.ImageField(upload_to='qr_codes', blank=True)

    delivery_area = ArrayField(models.CharField(max_length=200), blank=True)
    delivery_charge = models.PositiveIntegerField(default=0)
    delivery_time = models.CharField(max_length=120)
    tax_rate = models.CharField(max_length=120)
    tax_type = models.CharField(choices=TAX_TYPE_CHOICE, max_length=20)
    
    payment_methods = MultiSelectField(choices=PAYMENT_TYPE_CHOICE, max_length=100)
    table_numbers = ArrayField(models.CharField(max_length=255), blank=True)

    def __str__(self):
        return f"{self.name}"

    def get_qr_code(self):
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=15,
            border=3,
        )
        qr.add_data(f'{self.brand.subdomain}.onnow.io/{self.name.lower()}')
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        fname = f"qr_code_{self.name.lower()}.png"
        buffer = BytesIO()
        img.save(buffer, 'PNG')
        self.qr_code.save(fname, File(buffer))

    def __brand__(self):
        return self.brand.name

    def __brand_owner__(self):
        return self.brand.owner.user.name


class OpeningHoursOnDay(BaseModel):
    opening_from = models.TimeField()
    opening_to = models.TimeField()
    week_day = models.CharField(max_length=10)
    active_status = models.BooleanField(default=True)
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name='outlet_oh')

    class Meta:
        ordering = ('week_day', 'opening_from')
   

    def __str__(self):
        return f"{self.week_day}"  


class Menu(BaseModel):
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name



    #CTO UPDATE
    def __brand__(self):
        if self.brand is not None:
            return self.brand.name
        return None


class Item(BaseModel):
    menu = models.ForeignKey(Menu, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255)
    img = models.ImageField(upload_to='items', blank=True, null=True)
    description = models.TextField(max_length=1000, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return self.name


class Inventory(BaseModel):
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, null=True, related_name='inventory')
    is_available = models.BooleanField(default=True)
    pause_time = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.outlet.name}"

    def __brand__(self):
        return self.outlet.brand.name


class InventoryMenu(BaseModel):
    inventory = models.ForeignKey(Inventory, on_delete=models.SET_NULL, null=True, related_name='menu')
    menu = models.ForeignKey(Menu, on_delete=models.SET_NULL, null=True, related_name='menu')
    is_available = models.BooleanField(default=True)
    pause_time = models.PositiveIntegerField(default=0)


class InventoryItem(BaseModel):
    inventory_menu = models.ForeignKey(InventoryMenu, on_delete=models.SET_NULL, null=True, related_name='item')
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, related_name='item')
    is_available = models.BooleanField(default=True)
    pause_time = models.PositiveIntegerField(default=0)
    order_count = models.PositiveIntegerField(default=0)



def create_outlet_post_save(sender,instance, created, *args, **kwargs):
    if created:
        inventory = Inventory.objects.create(outlet=instance)
        inventory.save()
        try:
            menu = Menu.objects.filter(brand=instance.brand)
            print(menu)
            for m in menu:
                print(m)
                menu_obj = InventoryMenu.objects.create(inventory=inventory,menu=m)
                menu_obj.save()
                try:
                    item = Item.objects.filter(menu=m)
                    item_list = []
                    for i in item:
                        item_list.append(InventoryItem(inventory_menu=menu_obj,item=i))
                    objs = InventoryItem.objects.bulk_create(item_list)
                except:
                    pass

        except:
            pass


def create_menu_post_save(sender,instance, created, *args, **kwargs):
    if created:
        inventorys = Inventory.objects.filter(outlet__brand=instance.brand)
        i_list=[]
        for i in inventorys:
            i_list.append(InventoryMenu(inventory=i,menu=instance))
        objs = InventoryMenu.objects.bulk_create(i_list)


def create_item_post_save(sender,instance, created, *args, **kwargs):
    if created:
        menus = InventoryMenu.objects.filter(menu=instance.menu)
        m_list = []
        for i in menus:
            m_list.append(InventoryItem(inventory_menu=i,item=instance))
        objs = InventoryItem.objects.bulk_create(m_list)



post_save.connect(create_outlet_post_save, sender=Outlet)
post_save.connect(create_menu_post_save, sender=Menu)
post_save.connect(create_item_post_save, sender=Item)