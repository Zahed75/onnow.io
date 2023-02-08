from django_filters import rest_framework as filters

from orders.models import Order
from .models import Customer


class CustomerFilter(filters.FilterSet):
    customer_name = filters.CharFilter(field_name="customer__user__name", lookup_expr='icontains')
    phone = filters.CharFilter(field_name="customer__user__phone_number", lookup_expr='iexact')

    class Meta:
        model = Order
        fields = ['customer_name', 'phone']