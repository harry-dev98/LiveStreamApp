#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  8 11:52:24 2019

@author: harry
"""


# importing required modules/libraries..

import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt
import os
from datetime import datetime
from Preprocess.preprocess import *


class segments:

    """
        =>  input - a binary image..
        
        =>  operations - methods here dilate binary image accordingly, to
        get required segmentation.
        
        => output - segmented image, requiredContours, etc.
    
    """
    
    """
    initalizing this class with an image,
    3 kernels for dilating the image
    (we will use 2 to 3 iteratations of dilation),
    a counter keeping track of segmented images,
    """
    
    def __init__(self):
        
        self.binaryImg = None
        #counter to keep track of segmented images..
        self.numImg = 0
        
        # Kernals we will use...
        self.dilatingKernel = np.ones((250,250), np.uint8)
        self.lineDilatingKernel = np.ones((10,100), np.uint8)
        self.wordDilatingKernel = np.ones((15,50), np.uint8)
        self.charDilatingKernel = np.ones((3,5), np.uint8)
        self.dotDilatingKernel = np.ones((15,25), np.uint8)

        
        self.curDir = "/home/harry/DeepLearning/ZeddLabz/experiments"
        self.myDir = os.path.join(self.curDir, datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
        os.makedirs(self.myDir)
        os.makedirs(self.myDir+"/segments")
        os.makedirs(self.myDir+"/dilation")
        
    
   


    """
        segments the image by drawing rectangles on the image..        
    """        
    
    def getSegments(self, VP, threshold, isWord=False):
        
        indices = np.where(VP <= threshold)[0]
        index = []
        x = indices[0]
        s = x
        s_ = 0
        e = x

        for i in range(1, len(indices)):
            if indices[i] == x+1:
                e += 1
                x += 1
            else:
                index.append(int((s+e+1)/2))
                    
                x = indices[i]
                s_ = s
                s = x
                e = x

        index.append(int((s+e+1)/2))
        return index
    
    
    def SegmentImage(self, img, **kwargs):
        isLine = kwargs.pop("isLine", False)
        isChar = kwargs.pop("isChar", False)
        isWord = kwargs.pop("isWord", False)
        isClean = kwargs.pop("isClean", False)
        saveImg = kwargs.pop("saveImg", False)
        verbose = kwargs.pop("verbose", False)
        xW = kwargs.pop("xW", 1)
        xH = kwargs.pop("xH", 1)
        
        """
        Setting a threshold segmenting with getting vertical projections 
        and horizontal projections.
        """
        
        imgCopy = img.copy()
        H, W = img.shape
        if isLine:
            projection = np.sum(imgCopy, 1)
#             threshold = np.mean(projection)/6
            threshold = 0
            
        if isChar or isWord:
            projection = np.sum(imgCopy, 0)
            threshold = np.mean(projection)/6
            
        index = self.getSegments(projection, threshold, isWord=isWord)
        ROI = []
        
        for i in range(len(index)-1):
            if isLine:
                roi = self.binaryImg[index[i]:index[i+1], :]
                cv.rectangle(imgCopy,(0, index[i]+10),( W, index[i+1]-10),255,1)
            if isChar or isWord:
                roi = self.binaryImg[:, index[i]:index[i+1]]
                cv.rectangle(imgCopy,(index[i], 0),(index[i+1], H),255,1)
            if verbose:
                plt.imshow(roi,cmap='gray')
            if saveImg:
                self.saveImage(roi, "roi", i)
            if isClean:
                roi = preprocessing4ML(roi, xH, xW)
            ROI.append(roi)
        if saveImg:
            self.saveImage(imgCopy, "segmented")
            
        return imgCopy, ROI

    
    def SegmentImage_Dilated(self, imgDilated, **kwargs):
        height, width = imgDilated.shape
        saveImg = kwargs.pop("saveImg", False)
        verbose = kwargs.pop("verbose", False)
        isRmDot = kwargs.pop("isRmDot", False)
        H = kwargs.pop("H", 5)
        W = kwargs.pop("W", 5)
        thresholdH = kwargs.pop("thresholdH", 10)
        thresholdW = kwargs.pop("thresholdW", 10)
        
        if(len(kwargs)) != 0:
            raise Exception("Extra arguements passed")
        
        """
            input - (nparray)dilatedimage, 
            optional inputs - (bool)saveImg, (bool)verbose=>print segments,
                    (int)thresholdH, (int)thresholdW both are limits of 
                    rectangles on ROI
            output - (nparray)Segmented image,
                        (list)ROI
        
        """
        
        """
            Contours are the curves on the continous(same) pixels or intensity
            We use dilated image to get contours, in line segmentation contours
            will correspond to whole line all credits to dilation, similarly
            for word and char segemetation...
        """     
        
        #copying image..
        imgCopy = self.binaryImg.copy()
        imgDilated[imgDilated!=255] = 0
        
        # finding contours..
        ctrs, hier = cv.findContours(imgDilated.copy(), 
                                       cv.RETR_EXTERNAL, 
                                       cv.CHAIN_APPROX_SIMPLE)
        
        #sorting contours
        sorted_ctrs = sorted(ctrs, key=lambda ctr : cv.boundingRect(ctr)[0])

        # Required Region Of Intrest..
        ROI = []
        """
        Looping over all the contours found,
        check if they are required ROI then do the
        required, like drawing rectangles on ROI,
        saving image or showing progress, etc
        """

        for i, ctr in enumerate(sorted_ctrs): 
        
            # Get bounding box 
            x, y, w, h = cv.boundingRect(ctr)
                  
            r = self.binaryImg[y:y+h, x:x+w]
#             print(h,w)
            if isRmDot:
                n_white_pix = np.sum(r == 255)/(r.size)
                if (w < W and h < H and np.sum(r == 255) < 500) or n_white_pix<0.025:
                    imgCopy[y:y+h, x:x+w] = 0

            else:
                if (w > thresholdW and h > thresholdH):

                    # Getting ROI
                    roi = self.binaryImg[y:y+h, x:x+w]
                    cv.rectangle(imgCopy,(x,y),( x + w, y + h ),255,1)
                    if(verbose):
                        plt.imshow(roi,cmap='gray')
                    if(saveImg):
                        self.saveImage(roi, "roi", i)
                        
                    ROI.append(roi)
                    
        # saves the entire progress, i.e. the final segmented image
        if(saveImg):
            self.saveImage(imgCopy, "segmented")
            self.saveImage(imgDilated, "dilated")
        
        if(verbose):
            plt.imshow(imgCopy, cmap='gray')
            
        return imgCopy, ROI

    """
        Below 5 functions are similar...
        input - (bool)saveImg, (bool)Verbose, (int)dilationIter,
            (int)thresholdH, (int)thresholdW
        operations - dilates images and the find contours followed by ROI then
            saving or showing the progress as required.
        output - (nparray)Segmented image, (list)ROI
    """
    
    def removeDots(self, img, **kwargs):
        """
            Unpacking the arguements
            passed as a dict..
        """  
        self.binaryImg = img
        saveImg = kwargs.pop("saveImg", False)
        verbose = kwargs.pop("verbose", False)
        dilationIter=kwargs.pop("dilationIter", 2)
        H = kwargs.pop("H", 25)
        W = kwargs.pop("W", 25)
        
        self.binaryImg[self.binaryImg!=255] = 0
        imgDilated = cv.dilate(self.binaryImg, self.dotDilatingKernel, iterations=dilationIter)
        
        _, roi = self.SegmentImage_Dilated(imgDilated, isRmDot = True, saveImg = saveImg, H = H, W = W)
        
        
        return _

        
    
    def regionOfInterest(self, img, **kwargs):
        """
            Unpacking the arguements
            passed as a dict..
        """
        h, w = img.shape[:2]
        self.binaryImg = img.copy()
        
        saveImg = kwargs.pop("saveImg", False)
        verbose = kwargs.pop("verbose", False)
        dilationIter=kwargs.pop("dilationIter", 4)
        thresholdH = kwargs.pop("thresholdH", 300)
        thresholdW = kwargs.pop("thresholdW", w/2)
        
        self.binaryImg[self.binaryImg!=255] = 0
        imgDilated = cv.dilate(self.binaryImg, self.dilatingKernel, iterations=dilationIter)
        
        _, roi = self.SegmentImage_Dilated(imgDilated, thresholdH=thresholdH, thresholdW=thresholdW, saveImg=saveImg)
        
        return roi[0]

    

    #here after all need binary images
    
    def LineSegmentation(self, img, **kwargs):
        
        """
            Unpacking the arguements
            passed as a dict..
        """
        H, W = img.shape[:2]
        self.binaryImg = removeSkew(img)
        
        saveImg = kwargs.pop("saveImg", False)
        verbose = kwargs.pop("verbose", False)
                
        if(len(kwargs)) != 0:
            raise Exception("Extra arguements passed")
            
        
        return self.SegmentImage(self.binaryImg, isLine=True, saveImg=saveImg, verbose=verbose)

    
    def WordSegmentation(self, img, **kwargs):
        
        """
            Unpacking the arguements
            passed as a dict..
        """
        self.binaryImg = img
        saveImg = kwargs.pop("saveImg", False)
        verbose = kwargs.pop("verbose", False)
        dilationIter=kwargs.pop("dilationIter", 3)
        thresholdH = kwargs.pop("thresholdH", 50)
        thresholdW = kwargs.pop("thresholdW", 30)
        
        if(len(kwargs)) != 0:
            raise Exception("Extra arguements passed")
        
        imgDilated = cv.dilate(self.binaryImg, self.wordDilatingKernel, iterations=dilationIter)
        
        return self.SegmentImage_Dilated(imgDilated, thresholdH=thresholdH, thresholdW=thresholdW, saveImg=saveImg, verbose=verbose)
#         return self.SegmentImage(self.binaryImg, isWord=True, saveImg=saveImg, verbose=verbose)




    
    def CharSegmentation(self, img, **kwargs):
        
        """
            Unpacking the arguements
            passed as a dict..
        """
        
        xH = 1
        xW = 1
        saveImg = kwargs.pop("saveImg", False)
        isClean = kwargs.pop("isClean", True)
        verbose = kwargs.pop("verbose", False)
        
        if(len(kwargs)) != 0:
            raise Exception("Extra arguements passed")
        
        imgDilated = cv.dilate(img, np.ones((10,20), np.uint8), iterations=3)
        self.saveImage(imgDilated, "dilated")
        ctrs, hier = cv.findContours(imgDilated.copy(), 
                                       cv.RETR_EXTERNAL, 
                                       cv.CHAIN_APPROX_SIMPLE)
        x, y, w, h = cv.boundingRect(ctrs[-1])
        self.binaryImg = img[y:y+h, x:x+w]
        
        
        return self.SegmentImage(self.binaryImg, isChar=True, isClean=isClean, saveImg=saveImg, verbose=verbose, xH=xH, xW=xW)

    
    
    def saveImage(self, img, kind, i=-1):

        if kind == "roi":
            cv.imwrite(self.myDir+"/segments/img{}{}{}.jpeg".format(self.numImg,'_',i), img)
        elif kind=="segmented":
            cv.imwrite(self.myDir+"/segmentedImage{}.jpeg".format(self.numImg), img)
            self.numImg += 1
        else:
            cv.imwrite(self.myDir+"/dilation/dilatedImg{}.jpeg".format(self.numImg), img)
                       
        return
