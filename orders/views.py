import json

from django.db.models import Sum, Avg, Count
from django.shortcuts import render
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAdminUser,
    DjangoModelPermissions, DjangoObjectPermissions
)
from brands.models import Brand
from .serializer import *
from utils.custom_permission import IsOwner, IsBrandManager, LiveOrderHandle, IsCustomer
from utils.custom_mixin import GetSerializerClassMixin

from django_filters import rest_framework as filters

from .payment import call_amarpay


class LiveOrderFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="customer__user__name", lookup_expr='icontains')
    order_status = filters.CharFilter(field_name="order_status", lookup_expr='icontains')

    class Meta:
        model = Order
        fields = ['name', 'order_status']


class OrderHistoryFilter(filters.FilterSet):
    brand = filters.CharFilter(field_name="outlet__brand__name", lookup_expr='iexact')
    order_id = filters.CharFilter(field_name="order_id", lookup_expr='iexact')
    customer_name = filters.CharFilter(field_name="customer__user__name", lookup_expr='icontains')
    phone = filters.CharFilter(field_name="customer__user__phone_number", lookup_expr='iexact')
    outlet = filters.CharFilter(field_name="outlet__name", lookup_expr='icontains')
    payment = filters.CharFilter(field_name="payment_method", lookup_expr='icontains')
    order_type = filters.CharFilter(field_name="order_type", lookup_expr='icontains')
    channel = filters.CharFilter(field_name="channel", lookup_expr='icontains')
    order_status = filters.CharFilter(field_name="order_status", lookup_expr='icontains')

    start_date = filters.DateFilter(field_name="create_at", lookup_expr='gte')
    end_date = filters.DateFilter(field_name="create_at", lookup_expr='lte')

    class Meta:
        model = Order
        fields = ['brand', 'order_id', 'customer_name', 'phone', 'outlet', 'payment', 'order_type', 'channel',
                  'order_status', 'start_date', 'end_date']


class GetOrderHistory(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ReadOrderHistorySr
    permission_classes = [LiveOrderHandle]
    filterset_class = OrderHistoryFilter

    def get_queryset(self):
        user = self.request.user
        if user.user_type == "ACO":
            return Order.objects.filter(outlet__brand__owner__user=user)

        elif user.user_type == "MGR":
            return Order.objects.filter(outlet__brand__manager__user=user)

        else:
            return Order.objects.filter(outlet__outlet_manager__user=user)


class GetLiveOrderView(mixins.RetrieveModelMixin,
                       mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    lookup_field = 'order_id'
    serializer_class = ReadLiveOrderSr
    permission_classes = [LiveOrderHandle]
    filterset_class = LiveOrderFilter

    def get_queryset(self):
        user = self.request.user
        if user.user_type == "ACO":
            return Order.objects.filter(outlet__brand__owner__user=user)

        elif user.user_type == "MGR":
            return Order.objects.filter(outlet__brand__manager__user=user)

        else:
            return Order.objects.filter(outlet__outlet_manager__user=user)


class PlaceOrder(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = CustomerPlaceOrder
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsCustomer]
    queryset = Order.objects.all()


class CustomerOrderListFilter(filters.FilterSet):
    outlet = filters.CharFilter(field_name="outlet__name", lookup_expr='iexact')

    class Meta:
        model = Order
        fields = ['outlet']


class CustomerOrders(GetSerializerClassMixin, viewsets.ReadOnlyModelViewSet):
    lookup_field = 'order_id'
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsCustomer]
    filterset_class = CustomerOrderListFilter

    serializer_action_classes = {
        'retrieve': CustomerOrderDetailsSr,
        'list': CustomerOrderListSr
    }

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(customer__user=user)


def processDashboardQuery(order):
    total_order = order.count()
    calculated_value = order.aggregate(total_sales=Sum('total'), avg_busket=Avg('total'))

    # outlet overview
    order_by_outlet = order.values('outlet__name').annotate(Sum('total'))

    # new vs ret
    count_order_qs = order.values('customer_id').annotate(Count('customer_id')).values('customer_id',
                                                                                       'customer_id__count',
                                                                                       'total')  # filter(customer_id__count=2).annotate(Sum('total'),Avg('total')).annotate(Count('customer_id', distinct=True))

    new_order = count_order_qs.filter(customer_id__count=1)
    count_new_order = new_order.count()
    count_ret_order = total_order - count_new_order
    count_new_customer = count_new_order
    base_ret_customer = count_order_qs.filter(customer_id__count__gte=2)
    ret_customer = base_ret_customer.annotate(ret_customer=Count('customer__id', distinct=True)).aggregate(
        Count('ret_customer'))
    # count_ret_customer = ret_customer
    count_ret_customer = ret_customer["ret_customer__count"]
    percentage_new_customer = (count_new_customer / (count_ret_customer + count_new_customer)) * 100
    percentage_ret_customer = 100 - percentage_new_customer
    total_new_order = new_order.aggregate(Sum('total'), Avg('total'))
    total_ret_order = base_ret_customer.aggregate(Sum('total'), Avg('total'))

    percentage_new_order = (count_new_order / total_order) * 100
    percentage_ret_order = 100 - percentage_new_order

    return {
        "overview": {
            "total_order": total_order,
            "total_sales": calculated_value["total_sales"],
            "avg_basket_value": calculated_value["avg_busket"]
        },
        "total_order_by_outlet": order_by_outlet,
        "new_customer": {
            "num_orders": count_new_order,
            "num_customers": count_new_customer,
            "percentage_customers": percentage_new_customer,
            "avg_basket": total_new_order["total__avg"],
            "total": total_new_order["total__sum"],
            "percentage_new_order": percentage_new_order
        },
        "ret_customer": {
            "num_orders": count_ret_order,
            "num_customers": count_ret_customer,
            "percentage_customers": percentage_ret_customer,
            "avg_basket": total_ret_order["total__avg"],
            "total": total_ret_order["total__sum"],
            "percentage_new_order": percentage_ret_order
        }
    }


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsOwner | IsBrandManager])
def dashboard(request, brand=None):
    try:
        if request.user.user_type == "ACO":
            order = Order.objects.filter(outlet__brand__owner__user=request.user)
        elif request.user.user_type == "MGR":
            # inner_qs = Brand.objects.filter()
            # entries = Entry.objects.filter(blog__in=inner_qs)
            order = Order.objects.filter(outlet__brand__manager__user__in=[request.user])
        else:
            order = Order.objects.filter(outlet__outlet_manager__user__in=[request.user])
        if order.exists():
            if brand is not None:
                order = order.filter(outlet__brand__name=brand)
            data = processDashboardQuery(order)
            return Response(status=status.HTTP_200_OK, data=data)
        else:
            return Response(status=status.HTTP_200_OK)

    except:
        return Response(
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsCustomer])
def paynow(request):
    response = call_amarpay(request.data)
    # if response.text["result"]:
    #     return Response(status=status.HTTP_200_OK, data=response.text)
    return Response(status=status.HTTP_200_OK, data=response.json())


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsOwner | IsBrandManager])
def sourceCount(request):
    try:
        if request.user.user_type == "ACO":
            order = Order.objects.filter(outlet__brand__owner__user=request.user)
        elif request.user.user_type == "MGR":
            order = Order.objects.filter(outlet__brand__manager__user__in=[request.user])
        else:
            order = Order.objects.filter(outlet__outlet_manager__user__in=[request.user])
        if order.exists():
            outlet, start_date, end_date, brand = False, False, False, False
            try:
                start_date = request.GET['start_date']
            except:
                pass
            try:
                end_date = request.GET['end_date']
            except:
                pass
            try:
                brand = request.GET['brand']
            except:
                pass
            try:
                outlet = request.GET['outlet']
            except:
                pass
            if outlet:
                order = order.filter(outlet__name=outlet)

            elif not outlet and brand:
                order = order.filter(outlet__brand__name=brand)

            if start_date and end_date:
                order = order.filter(date__range=[start_date, end_date])

            mobile_order = order.filter(channel='Mobile')
            web_order = order.filter(channel='Web')
            mobile_order = mobile_order.values('date').annotate(Count('channel')).values('date', 'channel__count',
                                                                                         'channel')
            web_order = web_order.values('date').annotate(Count('channel')).values('date', 'channel__count',
                                                                                   'channel')
            return Response(status=status.HTTP_200_OK, data={
                "mobile": mobile_order,
                "web": web_order
            })
        else:
            return Response(status=status.HTTP_200_OK)

    except:
        return Response(
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([LiveOrderHandle])
def editLiveOrder(request, order_id):
    data = request.data
    serializer = EditLiveOrder(data=data)
    if serializer.is_valid():
        try:
            order_obj = Order.objects.get(order_id=order_id)
            order_obj.order_status = data["order_status"]
            order_obj.save()

            order_tracker = OrderTracker.objects.create(order=order_obj,
                                                        order_status=data["order_status"],
                                                        title=data["title"])
            order_tracker.save()

            notification = Notification.objects.create(customer=order_obj.customer,
                                                       order_id=order_id,
                                                       order_status=data["order_status"],
                                                       title=data["title"])
            notification.save()

            return Response(status=status.HTTP_200_OK,
                            data={"msg": "edit live order done"})
        except:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={"msg": "No order found with this order id"}
            )

    else:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=serializer.errors
        )


class GetNotification(mixins.RetrieveModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsCustomer]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return Notification.objects.filter(customer__user=self.request.user)
