import os
import numpy as np
import cv2 as cv
import pytesseract
pass2=True
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\hennebertp\AppData\Local\Tesseract-OCR\tesseract.exe"
#mydir=r"E:\personal\EtudesEgyptologie\DigitalResearch\P2_wimmer\InputData\Plates"
mydir=r"E:\personal\EtudesEgyptologie\DigitalResearch\P2_wimmer\IntermediateData\PlatesRequiringPass2"
for i,r in enumerate(os.listdir(mydir)):
    print("Starting to process file {} ({})".format(i,r))
    if ("Pal" in r):
        img=cv.imread(mydir+"\\"+r)
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        value, thresh = cv.threshold(gray, 60, 255, cv.THRESH_BINARY_INV)
        kernel = np.ones((5, 5), np.uint8)
        thresh_d=cv.dilate(thresh,kernel,iterations=1)
        contours, hierarchy = cv.findContours(thresh_d, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        #find box with SETHOS I
        nSethos=0
        sethosTop=-1
        sethosRight=-1
        for k,c in enumerate(contours):
            x,y,w,h = cv.boundingRect(c)
            if x>160 and x<450 and y>850 and y<1350 and w>875 and w<1130 and h>520 and h<722:
                sOCR=pytesseract.image_to_string(thresh_d[y: y+h, x: x+w])
                if "ETHO" in sOCR:
                    nSethos+=1
                    sethosTop=y
                    sethosRight=x+w
                #cropped = img[y: y+h, x: x+w]
                #cv.imwrite(r"e:\personal\etudesegyptologie\DigitalResearch\sandbox\cont\c{}_{}_{}_{}_{}_{}.png".format(i,k,x,y,w,h),cropped)               
           #if w>500 and h>300 and w<5000 and h<3000:
               #cropped = img[y: y+h, x: x+w]
               #cv.imwrite(r"e:\personal\etudesegyptologie\DigitalResearch\sandbox\cont\c{}_{}_{}_{}_{}_{}.png".format(i,k,x,y,w,h),cropped)
        if nSethos!=1:
            print("nSethos = {} for {}".format(nSethos,r))
        else:
            (numLabels, labels, stats, centroids)=cv.connectedComponentsWithStats(thresh,8,cv.CV_32S)
            print("There are {} components".format(numLabels))
            #find the first non-background component almost as large as the image
            nGridLabel = -1
            bottomOfGrid=-1
            for jj in range(1, numLabels):
                h = stats[jj, cv.CC_STAT_HEIGHT]
                w = stats[jj, cv.CC_STAT_WIDTH]
                x = stats[jj, cv.CC_STAT_LEFT]
                y = stats[jj, cv.CC_STAT_TOP]
                if h>thresh.shape[0]*.07 and w>thresh.shape[1]*0.7:
                    nGridLabel=jj
                    bottomOfGrid=y+h
                    break
            if nGridLabel >-1:
                print("Found grid component {}".format(nGridLabel))
                #now we try to get rid of the vertical bulleted lines joining hieratograms of the same WImmer-type
                #Step 1: identify potential bullets
                potentialBullets=[] #array of integers - position in the list of components
                minWidthBullet=10
                maxWidthBullet=45
                minHeightBullet=10
                maxHeightBullet=45
                minVerticalDistanceBetweenBullets=59
                maxVerticalDistanceBetweenBullets=77
                maxHorizontalDistanceBetweenBullets=10
                thinSideMaxLimit=30
                tallSideMinLimit=500
                dirtAreaLimit=40
                
                for jj in range(1,numLabels):
                    x = stats[jj, cv.CC_STAT_LEFT]
                    w = stats[jj, cv.CC_STAT_WIDTH]
                    h = stats[jj, cv.CC_STAT_HEIGHT]
                    y = stats[jj, cv.CC_STAT_TOP]
                    if x>=sethosRight+5 and y>=sethosTop and \
                       minWidthBullet <= w <= maxWidthBullet and minHeightBullet<=h<=maxHeightBullet:
                        potentialBullets.append(jj)
                #Step 2: sort them by vertical position, top first
                potentialBullets.sort(key=lambda u : stats[u, cv.CC_STAT_TOP])
                #Step 3: identify each one and all of the connected ones just below
                minInAColumn=4
                confirmedBullets=[]
                while len(potentialBullets)>0:
                    bb1=potentialBullets[0]
                    curX=stats[bb1, cv.CC_STAT_LEFT]
                    curY=stats[bb1, cv.CC_STAT_TOP]
                    bulletsInThisColumn=[bb1]
                    #check all the other potentialBullets and find the one just below
                    mustContinueSearching=True
                    while mustContinueSearching:
                        mustContinueSearching=False
                        for bb2 in potentialBullets:
                            bb2X=stats[bb2, cv.CC_STAT_LEFT]
                            bb2Y=stats[bb2, cv.CC_STAT_TOP]
                            #if bb1==119:
                            #    print("comparing bb1 {} {}  to {} - {} {}".format(curX,curY,bb2, bb2X,bb2Y))
                            if curX-maxHorizontalDistanceBetweenBullets<=bb2X<=curX+maxHorizontalDistanceBetweenBullets and \
                               curY+minVerticalDistanceBetweenBullets<=bb2Y<=curY+maxVerticalDistanceBetweenBullets:
                                #found the bullet just below
                                bulletsInThisColumn.append(bb2)
                                curX=bb2X
                                curY=bb2Y
                                mustContinueSearching=True
                    if len(bulletsInThisColumn)>=minInAColumn:
                        for bb in bulletsInThisColumn:
                            confirmedBullets.append(bb)
                            potentialBullets.remove(bb)
                    else:
                        potentialBullets.remove(bb1)
                #print("Found {} confirmed bullets".format(len(confirmedBullets)))
                maskOfKept = np.zeros(thresh.shape, dtype="uint8")
                maskOfDiscarded = np.zeros(thresh.shape, dtype="uint8")
                maxWidthForGrapheme = 1800
                maxHeightForGrapheme = 1800
                maxWidthForGraphemePass2 = 4000
                nKept=0
                for jj in range(1, numLabels):
                    x = stats[jj, cv.CC_STAT_LEFT]
                    y = stats[jj, cv.CC_STAT_TOP]
                    w = stats[jj, cv.CC_STAT_WIDTH]
                    h = stats[jj, cv.CC_STAT_HEIGHT]
                    area = stats[jj, cv.CC_STAT_AREA]
                    blIsKept=False
                    blIsDirt=False
                    isThinHorOrVer = (w<thinSideMaxLimit and h>tallSideMinLimit) or (h<thinSideMaxLimit and w>tallSideMinLimit)
                    if x>=sethosRight+5 and y>=sethosTop and area>dirtAreaLimit and y<=bottomOfGrid and \
                           ((not(pass2) and w<=maxWidthForGrapheme and h<=maxHeightForGrapheme) or \
                            (pass2 and not(isThinHorOrVer) and w<maxWidthForGraphemePass2)) and  not(jj in confirmedBullets):
                        blIsKept=True
                        print("Keeping {} with area {}, w {}, h {} ".format(jj,area,w,h))
                        componentMask = (labels == jj).astype("uint8") * 255
                        #cv.imwrite(r"e:\personal\etudesegyptologie\DigitalResearch\sandbox\components\kept\c{}_{}_{}_{}_{}_{}.png".format(i,jj,x,y,w,h),componentMask[y: y+h, x: x+w])
                        maskOfKept = cv.bitwise_or(maskOfKept, componentMask)
                        nKept+=1
                    if area<=dirtAreaLimit:
                        #print("{} must be dirt because area {}".format(jj,area))
                        blIsDirt=True
                    if not(blIsDirt) and not(blIsKept):
                        #print("DIscarding {} with area {} ".format(jj,area))
                        componentMask = (labels == jj).astype("uint8") * 255
                        maskOfDiscarded = cv.bitwise_or(maskOfDiscarded, componentMask)
                    #if jj in confirmedBullets:
                    #    w = stats[jj, cv.CC_STAT_WIDTH]
                    #    h = stats[jj, cv.CC_STAT_HEIGHT]
                    #    cv.imwrite(r"e:\personal\etudesegyptologie\DigitalResearch\sandbox\components\bullets\c{}_{}_{}_{}_{}_{}_confirmedBullet.png".format(i,jj,x,y,w,h),componentMask[y: y+h, x: x+w])
                #cv.imwrite(r"E:\personal\EtudesEgyptologie\DigitalResearch\sandbox\masks\kept\{}.png".format(i),maskOfKept)
                cv.imwrite(r"E:\personal\EtudesEgyptologie\DigitalResearch\sandbox\masks\kept\{}.png".format(r),maskOfKept)
                cv.imwrite(r"E:\personal\EtudesEgyptologie\DigitalResearch\P2_Wimmer\IntermediateData\CleanedUpImages\{}.png".format(r),maskOfKept)
                #cv.imwrite(r"E:\personal\EtudesEgyptologie\DigitalResearch\sandbox\masks\discarded\{}.png".format(i),maskOfDiscarded)
                cv.imwrite(r"E:\personal\EtudesEgyptologie\DigitalResearch\sandbox\masks\discarded\{}.png".format(r),maskOfDiscarded)
                print("For image {}, kept {} components".format(i,nKept))
                        

