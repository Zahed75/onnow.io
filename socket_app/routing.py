from . import consumers
from django.urls import path,re_path



websocket_urlpatterns= [
    re_path(r'ws/onnow/(?P<order_id>\w+)/$', consumers.OrderStatusTrack.as_asgi())
]