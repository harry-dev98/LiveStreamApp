from django.urls import path, include

from .views import sectionWiseAPIView, test

urlpatterns = [
    path("", sectionWiseAPIView, name="stats"),
    path("test/", test, name="test_"),
]
