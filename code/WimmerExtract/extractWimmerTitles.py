import os
import numpy as np
import cv2 as cv
import math
import pytesseract

def get_grayscale(image):
    return cv.cvtColor(image, cv.COLOR_BGR2GRAY)

# noise removal
def remove_noise(image):
    return cv.medianBlur(image,5)
 
#thresholding
def thresholding(image):
    return cv.threshold(image, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)[1]

#dilation
def dilate(image):
    kernel = np.ones((5,5),np.uint8)
    return cv.dilate(image, kernel, iterations = 1)
    
#erosion
def erode(image):
    kernel = np.ones((5,5),np.uint8)
    return cv.erode(image, kernel, iterations = 1)

#opening - erosion followed by dilation
def opening(image):
    kernel = np.ones((5,5),np.uint8)
    return cv.morphologyEx(image, cv.MORPH_OPEN, kernel)

#canny edge detection
def canny(image):
    return cv.Canny(image, 100, 200)

#skew correction
def deskew(image):
    coords = np.column_stack(np.where(image > 0))
    angle = cv.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv.warpAffine(image, M, (w, h), flags=cv.INTER_CUBIC, borderMode=cv.BORDER_REPLICATE)
    return rotated

#template matching
def match_template(image, template):
    return cv.matchTemplate(image, template, cv.TM_CCOEFF_NORMED) 

outfilepath=r"e:\personal\etudesEgyptologie\digitalresearch\P2_Wimmer\IntermediateData\wimmertitles.txt"
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\hennebertp\AppData\Local\Tesseract-OCR\tesseract.exe"
mydir=r"E:\personal\EtudesEgyptologie\digitalresearch\P2_Wimmer\InputData\Plates"
for i,r in enumerate(os.listdir(mydir)):
    #print("File {} is {}".format(i,r))
    sCurLine=r
    if i>=3:
        img=cv.imread(mydir+"\\"+r)
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        value, thresh = cv.threshold(gray, 60, 255, cv.THRESH_BINARY_INV)
        kernel = np.ones((5, 5), np.uint8)
        thresh_d=cv.dilate(thresh,kernel,iterations=1)
        contours, hierarchy = cv.findContours(thresh_d, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        #find box with SETHOS I
        nSethos=0
        for k,c in enumerate(contours):
            x,y,w,h = cv.boundingRect(c)
            if x<500 and y<500 and w>5000 and h<1000:
            #if x<500 and y<3000:
                #print(pytesseract.image_to_string(thresh_d[y: y+h, x: x+w]))
                #print("For image {}, h<1000 is {}".format(k,h<1000))
                crop1=thresh_d[y:y+h,x:math.floor(x+0.4*w)]
                crop2=thresh_d[y:y+h,x+math.floor(0.6*w):x+w]
                s1=pytesseract.image_to_string(crop1, lang='eng', config="--psm 7")
                s2=pytesseract.image_to_string(crop2, lang='eng', config="--psm 7")
                sCurLine+="\t"+s1.replace("\n","")+"\t"+s2.replace("\n","")+"\n"
                cropped = img[y: y+h, x: x+w]
                cv.imwrite(r"e:\personal\etudesegyptologie\DigitalResearch\P2_Wimmer\IntermediateData\HeaderImages\{}_header.png".format(r),cropped)
                #cv.imwrite(r"e:\personal\etudesegyptologie\sandbox\cont\{}.png".format(r),cropped)
                break
        print("Writing {}".format(sCurLine))
        outfile=open(outfilepath,"a")
        outfile.write(sCurLine)
        outfile.close()
        """
        (numLabels, labels, stats, centroids)=cv.connectedComponentsWithStats(thresh,8,cv.CV_32S)
        print("There are {} labels".format(numLabels))
        #find the first non-background component almost as large as the image
        nGridLabel = -1
        for jj in range(1, numLabels):
            h = stats[jj, cv.CC_STAT_HEIGHT]
            w = stats[jj, cv.CC_STAT_WIDTH]
            if h>thresh.shape[0]*.07 and w>thresh.shape[1]*0.7:
                nGridLabel=jj
                break
        if nGridLabel >-1:
            print("Found component {}".format(nGridLabel))
            #componentMask = (labels == nGridLabel).astype("uint8") * 255
            #cv.imwrite(r"e:\personal\etudesegyptologie\sandbox\masks\{}.png".format(i),componentMask)
        """
