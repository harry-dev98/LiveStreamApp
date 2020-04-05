from segment.SegmentingImage import segments

import urllib

import cv2
import numpy as np
import os 

def prediction(img, mdl):
	ans = ['0','1','2','3','4','5','6','7','8','9']
	proba = mdl.predict_proba(img)
	classes = np.argmax(proba, axis=1)
	word = ""
	for i in classes:
		word+=ans[i]

	return word

def url2img(url):
	resp = urllib.request.urlopen(url)
	image = np.asarray(bytearray(resp.read()), dtype="uint8")
	image = cv2.imdecode(image, cv2.IMREAD_COLOR)
	return image

def ocr(url, mdl):
	# image = url2img(url)
	image = cv2.imread('test5.jpg')
	gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
	denoised = cv2.fastNlMeansDenoising(gray, 7, 35, 7)
	_,thresh = cv2.threshold(denoised,127,255,cv2.THRESH_BINARY_INV|cv2.THRESH_OTSU)
	thresh = cv2.dilate(thresh, np.ones((3,3), np.uint8), iterations=1)

	S1 = segments()
	img = S1.regionOfInterest(thresh)
	img_ = S1.removeDots(img)
	__, lines = S1.LineSegmentation(img_)
	
	linesArr = []
	for i, line in enumerate(lines):
		if i == 0:
			continue
		_line, words = S1.WordSegmentation(line)
		wordsArr = []
		for i, word in enumerate(words):
			if i == 0 or i == 1:
				continue
			_word, char = S1.CharSegmentation(word, isClean=True)
			char = np.asarray(char)
			word = prediction(char, mdl)
			wordsArr.append(word)
		linesArr.append(wordsArr)
	
	return linesArr
