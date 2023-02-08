from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.fields import DictField, CharField
from rest_framework.validators import UniqueValidator


from .models import Brand, Menu, Item, InventoryItem, InventoryMenu, Inventory, Outlet

# Base user model
User = get_user_model()


class CreateBrandSerializer(serializers.ModelSerializer):
    banner_img = serializers.ImageField()
    logo_img = serializers.ImageField()
    brand_color = serializers.RegexField("^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    text_color = serializers.RegexField("^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")
    subdomain = serializers.RegexField("^[A-Za-z0-9]+$")

    class Meta:
        model = Brand
        fields = ['name', 'subdomain', 'brand_color',
                  'text_color', 'banner_img', 'logo_img']
        extra_kwargs = {

            'name': {
                'validators': [
                    UniqueValidator(
                        queryset=Brand.objects.all()
                    )
                ]
            }

        }

    def validate(self, data):
        if "subdomain" in data:
            if Brand.objects.filter(subdomain=data['subdomain']).exists():
                raise serializers.ValidationError({"subdomain": "subdomain must be unique"})
        return data


class BrandOutletInfo(serializers.ModelSerializer):
    class Meta:
        model = Outlet
        fields = ['name', 'delivery_area']

class ListBrandSerializer(serializers.ModelSerializer):
    outlet_brands = BrandOutletInfo(many=True)
    class Meta:
        model = Brand
        fields = ['id', 'name', 'subdomain', 'banner_img', 'logo_img','outlet_number',
                  'brand_color','text_color','outlet_brands']




class DetailsBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'


class GetUserAllBrand(serializers.Serializer):
    my_brands = DictField(child=CharField())
    other_brands = DictField(child=CharField())

    def my_brands(self, obj):
        try:
            my_brand = Brand.objects.filter(owner__user=obj.user)
            my_brand = ListBrandSerializer(my_brand, many=True)
            return my_brand
        except:
            return None

    def other_brands(self, obj):
        try:
            other_brands = Brand.objects.filter(brand_beneficiary__user=obj.user)
            other_brands = ListBrandSerializer(other_brands, many=True)
            return other_brands
        except:
            return None

    class Meta:
        model = Brand
        fields = ['my_brands', 'other_brands']



class CreateMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = '__all__'


class CreateMenuItemSerializer(serializers.ModelSerializer):
    img = serializers.ImageField(required=False)
    class Meta:
        model = Item
        fields = ['id','menu','name','description','price','img']


class InventoryItemSr(serializers.ModelSerializer):
    item_name = serializers.SerializerMethodField('get_name')
    price = serializers.SerializerMethodField('get_price')

    # def get_name(self,obj):
    #     return obj.item.name

    # CTO UPDATE
    def get_name(self, obj):
        if obj.item is not None:
            return obj.item.name
        return None

    # CTO UPDATE

    # def get_price(self,obj):
    #     return obj.item.price
    def get_price(self, obj):
        if obj.item:
            return obj.item.price
        else:
            return None

    class Meta:
        model = InventoryItem
        fields = ['id','item_name','price','is_available']


class InventoryMenuSr(serializers.ModelSerializer):
    item = InventoryItemSr(many=True)
    menu_name = serializers.SerializerMethodField('get_name')

    # def get_name(self, obj):
    #     return obj.menu.name

    #CTO Update:
    def get_name(self, obj):
        if obj.menu is None:
            return None
        return obj.menu.name

    class Meta:
        model = InventoryMenu
        fields = ['id','menu_name','is_available','item']


class InventorySr(serializers.ModelSerializer):
    menu = InventoryMenuSr(many=True)
    outlet_name = serializers.SerializerMethodField('get_name')

    def get_name(self, obj):
        return obj.outlet.name

    class Meta:
        model = Inventory
        fields = ['id','outlet_name','is_available','menu']
        

class EditInventorySr(serializers.Serializer):
    id = serializers.IntegerField()
    is_available = serializers.BooleanField()
    pause_time = serializers.IntegerField()


class GetOutletProduct(serializers.ModelSerializer):
    menu_name = serializers.SerializerMethodField('get_menu_name')

    # def get_menu_name(self,obj):
    #     return obj.inventory_menu.menu.name

    #CTO UPDATE
    def get_menu_name(self, obj):
        try:
            return obj.inventory_menu.menu.name
        except AttributeError:
            return None

    class Meta:
        model = InventoryItem
        fields = ['item', 'is_available', 'pause_time','order_count','menu_name']
        depth = 1



class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Outlet
        fields = ['address', 'delivery_area']

class BrandSerializerSubdomain(serializers.ModelSerializer):
    outlet_brands = AreaSerializer(many=True,required=True)
    class Meta:
        model = Brand
        fields = [field.name for field in model._meta.fields]
        fields.append('outlet_brands')
