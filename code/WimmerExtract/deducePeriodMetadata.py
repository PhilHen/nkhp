import os
import numpy as np
import cv2 as cv
import pathlib

rootdir=r"c:\hieraproject"
graphemesdir=os.path.join(rootdir,"P2_wimmer","OutputData","graphemes")
outputtextfilepath=os.path.join(rootdir,"P2_wimmer","IntermediateData","graphemesByPeriod.txt")
periods=["Sethos I", \
         "Ramses II (1-25)", \
         "Ramses II (26-45)", \
         "Ramses II (46-67)", \
         "Merneptah", \
         "Amenmnesse", \
         "Sethos II", \
         "Siptah/Tawosret", \
         "Sethnachte", \
         "Ramses III (1-11)", \
         "Ramses III (12-21)", \
         "Ramses III (22-32)", \
         "Ramses IV", \
         "Ramses V", \
         "Ramses VI", \
         "Ramses VII", \
         "Ramses IX"]
#get all graphemes in array
arrGraphemes=[]
for r in os.listdir(graphemesdir):
    extension=pathlib.Path(r).suffix
    if extension==".svg":
        stem=pathlib.Path(r).stem
        arrGraphemes.append(stem)
periodByGrapheme={}

platesdir=os.path.join(rootdir,"P2_wimmer","InputData","Plates")
verticaloffset=600
stripewidth=600
for r in os.listdir(platesdir):
    if ("Pal" in r):
        img=cv.imread(os.path.join(platesdir,r))
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        value, thresh = cv.threshold(gray, 60, 255, cv.THRESH_BINARY_INV)
        goodsepsets=[]
        goodsepsetsx=[]
        for horizontaloffset in range(2000,7000,stripewidth):
            seps=[]
            verticalstripe=thresh[verticaloffset:12300,horizontaloffset:horizontaloffset+600]
            (numLabels, labels, stats, centroids)=cv.connectedComponentsWithStats(verticalstripe,8,cv.CV_32S)
            for jj in range(1, numLabels):
                y = stats[jj, cv.CC_STAT_TOP]
                w = stats[jj, cv.CC_STAT_WIDTH]
                h = stats[jj, cv.CC_STAT_HEIGHT]
                if w>stripewidth-30 and h<60:
                    #it's a separator
                    seps.append(y+verticaloffset+h/2)
            #print(seps)
            if len(seps)==19:
                goodsepsets.append(seps)
                goodsepsetsx.append(horizontaloffset+stripewidth/2)
        #Now, goodseps is an array of possible separator sets
        #The following code, commented out, checks that they are indeed good (not "too different" from each other, and in a sufficiently large number)
        #Careful inspection proves that they are -> commented out
        #we have to check if they are indeed good, i.e.
        #not "too different" from each other
        #if len(goodsepsets)<3:
        #    print("Problem with plate {} - not enough separator sets ({})".format(r,len(goodsepsets)))
        #    print(goodsepsetsx)
        #    print(goodsepsets)
        #else:
        #    #sumDiff=0
        #    maxDiff=0
        #    for ii in range(1,len(goodsepsets)):
        #        for jj in range(0,len(goodsepsets[0])):
        #            curDiff=abs(goodsepsets[0][jj]-goodsepsets[ii][jj])
        #            #sumDiff+=curDiff
        #            if curDiff>maxDiff:
        #                maxDiff=curDiff
        #    #avgDiff=sumDiff/(len(goodsepsets)-1)/len(goodsepsets[0])
        #    #checked that avgDiff are all < 20, which seems reasonable, but skew must be computed
        #    if maxDiff>50:
        #        print("Plate {} has {} good separator sets, maxDiff is {}".format(r,len(goodsepsets),maxDiff))
        #        print(goodsepsets)
        #        print(goodsepsetsx)
        if len(goodsepsets)>0:
            #compute reference_separators and skew
            #reference_separators are separators at x=0, taking skew into account
            if len(goodsepsets)==1:
                skew=0
                reference_separators=goodsepsets[0]
            else:
                rightmosty=goodsepsets[len(goodsepsets)-1][len(goodsepsets[0])-1]
                leftmosty=goodsepsets[0][len(goodsepsets[0])-1]
                rightmostx=goodsepsetsx[len(goodsepsets)-1]
                leftmostx=goodsepsetsx[0]
                #print("rightmosty {}, leftmosty {}, rightmostx {}, leftmostx {}".format(rightmosty,leftmosty,rightmostx,leftmostx))
                skew=(rightmosty-leftmosty)/(rightmostx-leftmostx)
                reference_separators=[]
                for jj in range(0,len(goodsepsets[0])):
                    reference_separators.append(goodsepsets[0][jj]-leftmostx*skew)
            #print("skew {}, reference_separators {}".format(skew,reference_separators))
            #print("goodsepsets {}, goodsepsetsx {}".format(goodsepsets,goodsepsetsx))
            #Now, let's list all hieratograms belonging to the current plate and deduce periodmetadata for each
            stemPlate=pathlib.Path(r).stem
            stemPlate=stemPlate[0:len(stemPlate)-4] #remove "_Pal" at the end
            print(stemPlate)
            for g in arrGraphemes:
                if g.startswith(stemPlate+"_"):
                    a=g.split("_")
                    #xCenter=int(a[4])
                    #yCenter=int(a[5])
                    yAtx0=int(a[5])-int(a[4])*skew
                    #print("{} has x,y {},{} , skew is {} so y at x=0 is {}".format(g,xCenter,yCenter,skew,yAtx0))
                    period=""
                    for jj in range(1,len(reference_separators)-1):
                        #first two separators are close by - nothing in between
                        #print("At {}, comparing {} with {} and {}".format(jj,yAtx0,reference_separators[jj],reference_separators[jj+1]))
                        if yAtx0>reference_separators[jj] and yAtx0<reference_separators[jj+1]:
                            period=periods[jj-1]
                            break
                    if period!="":
                        periodByGrapheme[g]=period
                    else:
                        print("Cannot date {}".format(g))
                        #print("Reference separators are {}".format(reference_separators))
                        #print("Skew is {}".format(skew))
                    
#Now save everything to a text file
sResult=""
for k,v in periodByGrapheme.items():
    sResult+=k+"\t"+v+"\r"
textfile=open(outputtextfilepath,'wb')
textfile.write(sResult.encode("utf8"))
textfile.close()
                        
                    
            
            
            

