from django.urls import path
from .consumers import consumer, docConsumer, videoConsumer

websocket_urlpatterns = [
    path('ws/rooms/<str:name>/<str:identity>', consumer),
    path('ws/videos/<str:sess>', videoConsumer),
    path('ws/doc/<str:sess>', docConsumer),
]