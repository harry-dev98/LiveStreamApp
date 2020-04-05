from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

from .serializers import OCRSerializer
from .models import OCRData

import requests
import json

import cv2 as cv
import numpy as np
import os

from .apps import ApisConfig as OCR



@api_view(['GET',])
def OCRAPIView(request):
	data = request.GET
	print(data)
	
	url = json.loads(data['url'])
	ocr = OCR(url)
	ocrText = json.dumps(ocr._util())
	return_data = {
			"_class" : data["_class"],
			"section" : data["section"],
			"ocrText" : ocrText,
		}
	return Response(return_data)

# @api_view(['GET',])
def testView(request):
	url = "http://localhost/demo/view/admin/ocrs/test5.jpg"
	data = {
		"_class": json.dumps(12),
		"section" : json.dumps("lily"),
		"url" : json.dumps(url)
		# "url" : json.dumps("http://156.67.219.222/media/tests.jpg")
	}
	r = requests.get("http://127.0.0.1:8000/api/ocr/", params=data)
	# r = requests.get("http://156.67.219.222/api/ocr/", params=data)
	# print((r.text))
	return HttpResponse(r)