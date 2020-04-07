from django.urls import path
from .consumers import consumer

websocket_urlpatterns = [
    path('ws/rooms/<str:name>/<str:identity>', consumer),
]