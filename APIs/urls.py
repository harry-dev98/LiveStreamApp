from django.urls import path, include

from .views import OCRAPIView, testView

urlpatterns = [

    path("ocr/", OCRAPIView, name='ocrview'),
    path("test/", testView, name='testview'),

]
