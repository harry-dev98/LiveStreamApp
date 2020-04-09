from django.urls import path

from .views import *

urlpatterns = [
    path("", webinar),
    path("<str:sessid>/status", viewPeer, name="viewpeer"),
    path("<str:name>/host/", hostlogin, name='hostlogin'),
    path("<str:name>/peer/", peerlogin, name='peerlogin'),
    path("<str:name>/peer/<int:id>/", peer, name="peer"),
    path("<str:name>/host/<int:id>/", host, name='host'),
    path("404/", http404, name="404"),
    path("sessions/", viewSession, name="sessions"),
]
