from django.urls import path
from .consumers import consumer, docConsumer, msgConsumer

websocket_urlpatterns = [
    path('ws/rooms/<str:name>/<str:identity>/signal', consumer),
    path('ws/rooms/<str:name>/doc', docConsumer),
    path('ws/rooms/<str:name>/<str:identity>/msg', msgConsumer)
]