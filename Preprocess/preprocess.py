# ...

import cv2 as cv
import numpy as np
from skimage.morphology import thin
import math

def preprocessing4ML(invB, xH, xW):
    d = denoiseImage(invB)
#     dil = dilate(d, 3, 3, 1)
    rszd = resize(d, timesH=1/xH, timesW=1/xW)
    pad = padding(rszd, 0, 5, 15)
    rszd = resize(pad, height=28, width=28)
    norm = (rszd-rszd.mean())/rszd.std()
    blur = gaussianBlur(norm, 3, 3)
    rshpd = blur.reshape(28,28,1)
    return rshpd


def padding(img, pixel, x=62, y=62):
    X, Y = img.shape
    
#     x = int((pixelX-x-5)/2) if pixelX-x>5 else 0
#     y = int((pixelY-y-5)/2) if pixelY-y>5 else 0
    if X < 70:
        x += 70-X
    if Y < 70:
        y += 70-Y
        
    pad = np.pad(img, ((x,x),(y,y)), 'constant', constant_values=pixel)
    return resize(pad, width=62, height=62)
    

def gaussianBlur(img, kernelX=3, kernelY=3):
    blur = cv.GaussianBlur(img,(kernelX, kernelY),0)
    return blur
#     return img

def dilate(img, kernelX=3, kernelY=3, it=1):
    kernel = np.ones((kernelX, kernelY), np.uint8) 
    return cv.dilate(img, kernel, iterations=it)
    


def resize(img, **kwargs):
    width = kwargs.pop('width', -1)
    height = kwargs.pop('height', -1)
    timesW = kwargs.pop('timesW', -1)
    timesH = kwargs.pop('timesH', -1)
    
    if(len(kwargs)>0):
        raise "Extra Arguements Passed.."
    
    if width == -1 and height == -1:
        width = int(img.shape[1] * timesW)
        height = int(img.shape[0] * timesH)

    dim = (width, height)
    # resize image
    return cv.resize(img, dim, interpolation = cv.INTER_CUBIC) 


def denoiseImage(image, templateWindowSize=7, templateSearchSize=21, h=7 ):
    return cv.fastNlMeansDenoising(image, templateWindowSize, templateSearchSize, h) 


def color2gray(color):
    return cv.cvtColor(color,cv.COLOR_BGR2GRAY)
    

def gray2invBinary(gray):
    _, invBin = cv.threshold(gray,127,255,cv.THRESH_BINARY_INV|cv.THRESH_OTSU)
    return invBin


def gray2binary(gray):
    _, binary = cv.threshold(gray,127,255,cv.THRESH_BINARY|cv.THRESH_OTSU)
    return binary


def basicPreprocess(image):
    img = image.copy()
    if len(img.shape) == 3:
        gray = color2gray(img)
    else:
        gray = img
    denoised = denoiseImage(gray)
    binary = gray2invBinary(denoised)
    
#     blur = gaussianBlur(binary)
    return binary
    


def removeSkew(img):
    binaryImg = img.copy()
#     return deskew(binaryImg, compute_skew(binaryImg))
#     binaryImg = basicPreprocess(orgImg)
    
    # grab the (x, y) coordinates of all pixel values that
    # are greater than zero, then use these coordinates to
    # compute a rotated bounding box that contains all
    # coordinates
    coords = np.column_stack(np.where(binaryImg > 0))
    angle = cv.minAreaRect(coords)[-1]
    # the `cv2.minAreaRect` function returns values in the
    # range [-90, 0); as the rectangle rotates clockwise the
    # returned angle trends to 0 -- in this special case we
    # need to add 90 degrees to the angle
    if angle < -45:
        angle = -(90 + angle)

    # otherwise, just take the inverse of the angle to make
    # it positive
    else:
        angle = -angle
    
    if angle < 20:
        angle = angle/3
    # rotate the image to deskew it
    (h, w) = binaryImg.shape[:2]
    center = (w // 2, h // 2)
    M = cv.getRotationMatrix2D(center, angle, 1.0)
    binRotated = cv.warpAffine(binaryImg, M, (w, h), flags=cv.INTER_CUBIC, 
                            borderMode=cv.BORDER_REPLICATE)
#     orgRotated = cv.warpAffine(orgImg, M, (w, h), flags=cv.INTER_CUBIC, 
#                             borderMode=cv.BORDER_REPLICATE)
#     # draw the correction angle on the image so we can validate it
#     cv.putText(rotated, "Angle: {:.2f} degrees".format(angle), (10, 30), 
#                 cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    return binRotated
    
    

def compute_skew(src):
    
    #load in grayscale:
#     src = cv2.imread(file_name,0)
    height, width = src.shape[0:2]
    
    #invert the colors of our image:
#     cv2.bitwise_not(src, src)
    
    #Hough transform:
    minLineLength = width/2.0
    maxLineGap = 20
    lines = cv.HoughLinesP(src,1,np.pi/180,100,minLineLength,maxLineGap)
    
    #calculate the angle between each line and the horizontal line:
    angle = 0.0
    nb_lines = len(lines)
    
    
    for line in lines:
        angle += math.atan2(line[0][3]*1.0 - line[0][1]*1.0,line[0][2]*1.0 - line[0][0]*1.0);
    
    angle /= nb_lines*1.0
    
    return angle* 180.0 / np.pi


def deskew(img,angle):
    print(angle)
    #compute the minimum bounding box:
    non_zero_pixels = cv.findNonZero(img)
    center, wh, theta = cv.minAreaRect(non_zero_pixels)
    
    root_mat = cv.getRotationMatrix2D(center, angle, 1)
    rows, cols = img.shape
    rotated = cv.warpAffine(img, root_mat, (cols, rows), flags=cv.INTER_CUBIC)


    #Border removing:
    sizex = np.int0(wh[0])
    sizey = np.int0(wh[1])
    print(theta)
    if theta > -45 :
        temp = sizex
        sizex= sizey
        sizey= temp
    return cv.getRectSubPix(rotated, (sizey,sizex), center)
  

def removeLines(img):
    result = img.copy()
    # Remove horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (100,1))
    remove_horizontal = cv2.morphologyEx(invBin, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
    cnts = cv2.findContours(remove_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv2.drawContours(result, [c], -1, 0, 5)

    # Remove vertical lines
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1,45))
    remove_vertical = cv2.morphologyEx(invBin, cv2.MORPH_OPEN, vertical_kernel, iterations=1)
    cnts = cv2.findContours(remove_vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv2.drawContours(result, [c], -1, 0, 5)
    return result