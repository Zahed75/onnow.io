"""
ASGI config for onnow project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os
from channels.routing import ProtocolTypeRouter,URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path
from django.core.asgi import get_asgi_application
from socket_app import routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'onnow.settings')

application = get_asgi_application()


application = ProtocolTypeRouter({
    "http": application,
    "websocket": AllowedHostsOriginValidator(
    AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    )
),
})
