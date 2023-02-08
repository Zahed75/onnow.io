from django.urls import path, include

from .views import *
from .models import *
from rest_framework import routers

router = routers.DefaultRouter()

router.register('brand',BrandCRUD, basename='brand')
router.register('brand_by_subdomain', BrandBySubdomain)
router.register('other_brand',OtherBrand)
router.register('menu',MenuCRUD)
router.register('menu_item',MenuItemCRUD)
router.register('get_inventory',GetInventoryView),
router.register('outlet_products', OutletItem)

# urlpatterns = router.urls



urlpatterns = [
    path('', include(router.urls)),
    path('add_other_brand/', add_other_brand),
    path('remove_other_brand/', remove_other_brand),
    path('get_all_brands/',get_all_brand), #owner
    path('edit_outlet_inventory/',edit_outlet_inventory),
    path('edit_menu_inventory/',edit_menu_inventory),
    path('edit_item_inventory/',edit_item_inventory)
]
