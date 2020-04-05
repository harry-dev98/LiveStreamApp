from django.urls import path

from .views import *

urlpatterns = [
    path("", webinar),
    path("<str:name>/host/", host),
    path("<str:name>/peer/", peer),
]
