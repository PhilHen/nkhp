import os
import subprocess
import numpy as np
import cv2 as cv
import pytesseract
import pickle
import scipy
import easygui
import shutil

#----------------------------------
#     helper functions
#----------------------------------

def minDistance(contour, contourOther):
    distanceMin = 99999999
    for c0 in contour:
        for c1 in contourOther:
            xA=c0[0][0]
            xB=c1[0][0]
            yA=c0[0][1]
            yB=c1[0][1]
            distance = ((xB-xA)**2+(yB-yA)**2) # squared distance formula
            if (distance < distanceMin):
                distanceMin = distance
    return distanceMin**(1/2)


def haveIntersection(a,b):
    #a, b are 4-integer lists with edge coordinates [left, right, top, bottom]
    return (min(a[1],b[1])-max(a[0],b[0])>0) and (min(a[3],b[3])-max(a[2],b[2])>0)
    

def rectSpacing(r1,r2):
    d=max(abs(r1[0]+r1[2]/2-r2[0]-r2[2]/2)-(r1[2]+r2[2])/2,abs(r1[1]+r1[3]/2-r2[1]-r2[3]/2)-(r1[3]+r2[3])/2)
    if d<=0:
        d=0
    return d

def graphemeEdges(g,conts):
    #conts must be the dict of contours
    return [min([cv.boundingRect(conts[i])[0] for i in g]), \
                   max([cv.boundingRect(conts[i])[0] + cv.boundingRect(conts[i])[2] for i in g]), \
                   min([cv.boundingRect(conts[i])[1] for i in g]), \
                   max([cv.boundingRect(conts[i])[1] + cv.boundingRect(conts[i])[3] for i in g]) ]


def getDistanceMatrix(numLabels,conts,slowMode):
    #conts must be the dict of contours
    #if slowMode==True, use real distance ; other wise, just use bounding rectangles
    distances=np.zeros((numLabels,numLabels))
    for ii in range(1,numLabels):
        #print("Computing distances from {}".format(ii))
        for jj in range (1,ii):
            if slowMode:
                distances[ii,jj]=minDistance(contours[ii],contours[jj])
            else:
                distances[ii,jj]=rectSpacing(cv.boundingRect(contours[ii]),cv.boundingRect(contours[jj]))
            distances[jj,ii]=distances[ii,jj]
    return distances

#--------------------------------------------
# prepare picture
#--------------------------------------------
def getComponentsAndContours(bwPicture,cachefile):
    (nl, l, _, _)=cv.connectedComponentsWithStats(bwPicture,8,cv.CV_32S)
    print("There are {} components".format(nl))
    #first, compute a contour for each connected component "label"
    if os.path.exists(cachefile):
        f=open(cachefile,"rb")
        conts=pickle.load(f)
        f.close()
    else:
        conts={}
        for ii in range(1,nl):
            componentMask = (l == ii).astype("uint8") * 255
            #outCompFile=r"E:\personal\EtudesEgyptologie\DigitalResearch\sandbox\components\{}.png".format(ii)
            print("Finding contours for component {}".format(ii))
            #cv.imwrite(outCompFile,componentMask)
            c, _ = cv.findContours(componentMask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
            conts[ii]=c[0]
        f=open(cachefile,"wb")
        pickle.dump(conts,f)
        f.close()
    return nl,l,conts
    
#-----------------------------------
# display helper functions
#--------------------------------------

def getViewportFactor():
    return (curViewPort[1]-curViewPort[0])/xsizeOfDisplayWindow


def displayInViewport(l,g,ng,di):
    #vp=[xmin,xmax,ymin,ymax]
    #g = grapheme to display in one color (list of component indexes), ng=next grapheme to display in another color
    #di = list of components to display in another color
    croppedLabels=l[curViewPort[2]:curViewPort[3],curViewPort[0]:curViewPort[1]]
    channel1 = np.zeros(croppedLabels.shape,dtype="uint8")
    channel2 = np.zeros(croppedLabels.shape,dtype="uint8")
    channel3 = np.zeros(croppedLabels.shape,dtype="uint8")
    print("After defining channels")
    for c in list(range(1,numLabels)):
        br=cv.boundingRect(contours[c])
        bre=[br[0],br[0]+br[2],br[1],br[1]+br[3]]
        if haveIntersection(curViewPort,bre):
            print("Before computing component mask")
            componentMaskCropped=((labels == c).astype("uint8") * 255)[curViewPort[2]:curViewPort[3],curViewPort[0]:curViewPort[1]]
            print("After computing component mask")
            if c in g:
                channel1 = cv.bitwise_or(channel1, componentMaskCropped)
            elif c in ng:
                channel1 = cv.bitwise_or(channel1, componentMaskCropped)
                channel2 = cv.bitwise_or(channel2, componentMaskCropped)
            elif c in di:
                channel2 = cv.bitwise_or(channel2, componentMaskCropped)
            else:
                channel3 = cv.bitwise_or(channel3, componentMaskCropped)
            #outputImg = cv.bitwise_or(outputImg, componentMaskCropped)
            print("After bitwise_or")
            print ("Computed for {}".format(c))
    ysize=int((curViewPort[3]-curViewPort[2])/getViewportFactor())
    outputImg=cv.merge((channel1,channel3,channel2))
    outputImg=cv.resize(outputImg,(ysize,xsize))
    cv.imshow("aaa",outputImg)
    cv.waitKey()
    return outputImg

def displayInViewportLowRes(lowResLabs,g,ng,di,lowResFactor,windowName):
    #lowResLabs = labels array, in low resolution (with factor lowResFactor=4 to convert 1200 dpi to 300 dpi)
    #g = grapheme to display in one color (list of component indexes), ng=next grapheme to display in another color
    #di = list of components to display in another color
    croppedLowResLabels=lowResLabs[int(curViewPort[2]/lowResFactor):int(curViewPort[3]/lowResFactor),int(curViewPort[0]/lowResFactor):int(curViewPort[1]/lowResFactor)]
    channel1 = np.zeros(croppedLowResLabels.shape,dtype="uint8")
    channel2 = np.zeros(croppedLowResLabels.shape,dtype="uint8")
    channel3 = np.zeros(croppedLowResLabels.shape,dtype="uint8")
    for c in list(range(1,numLabels)):
        br=cv.boundingRect(contours[c])
        bre=[br[0],br[0]+br[2],br[1],br[1]+br[3]]
        if haveIntersection(curViewPort,bre):
            componentMaskCropped=((lowResLabs == c).astype("uint8") * 255)[int(curViewPort[2]/lowResFactor):int(curViewPort[3]/lowResFactor),int(curViewPort[0]/lowResFactor):int(curViewPort[1]/lowResFactor)]
            if c in g:
                channel1 = cv.bitwise_or(channel1, componentMaskCropped)
            elif c in ng:
                channel1 = cv.bitwise_or(channel1, componentMaskCropped)
                channel2 = cv.bitwise_or(channel2, componentMaskCropped)
            elif c in di:
                channel3 = cv.bitwise_or(channel3, componentMaskCropped)
            else:
                channel2 = cv.bitwise_or(channel2, componentMaskCropped)
    ysize=int((curViewPort[3]-curViewPort[2])/getViewportFactor())
    outputImg=cv.merge((channel1,channel2,channel3))
    outputImg=cv.resize(outputImg,(ysize,xsizeOfDisplayWindow))
    cv.imshow(windowName,outputImg)
    return outputImg

def displayRowOfText(img,nRow,sText,tColor):
    cv.putText(img,sText,(0,nRow*25),cv.FONT_HERSHEY_SIMPLEX,0.7,tColor,1,cv.LINE_AA,False)

def updateStatusWindow():
    img = np.zeros((800,600,3), np.uint8)
    curModeDescription=""
    if curMode=="d":
        curModeDescription="Mode d=discard selected components"
    elif curMode=="t":
        curModeDescription="Mode t=take selected components for current grapheme"
    elif curMode=="n":
        curModeDescription="Mode n=attribute selected components to next grapheme"
    elif curMode=="c":
        curModeDescription="Mode c=create new grapheme with selected components, set as next"
    displayRowOfText(img,1,curModeDescription,(255,255,255))
    displayRowOfText(img,2,"#graphemes: {}".format(len(graphemes)),(255,255,255))
    displayRowOfText(img,3,"#components: {}".format(numLabels),(255,255,255))
    displayRowOfText(img,4,"cur grapheme: {} ({} components)".format(curGrapheme,len(graphemes[curGrapheme])),(255,0,0))
    displayRowOfText(img,5,"next grapheme: {} ({} components)".format(nextGraphemeNumber(),len(graphemes[nextGraphemeNumber()])),(255,255,0))
    displayRowOfText(img,6,"#components discarded: {}".format(len(discarded)),(0,0,255))
    displayRowOfText(img,7,"left-right arrow = previous/next grapheme",(255,255,255))
    displayRowOfText(img,8,"a = discard all from cur grapheme",(255,255,255))
    displayRowOfText(img,9,"q = quit",(255,255,255))
    displayRowOfText(img,10,"n = mode 'attribute to next grapheme'",(255,255,255))
    displayRowOfText(img,11,"t = mode 'take for current grapheme'",(255,255,255))
    displayRowOfText(img,12,"d = mode 'discard'",(255,255,255))
    displayRowOfText(img,13,"c = mode 'create new and assign selected to it'",(255,255,255))
    displayRowOfText(img,14,"s = save",(255,255,255))
    displayRowOfText(img,15,"l = load",(255,255,255))
    displayRowOfText(img,16,"r = next unprocessed plate",(255,255,255))
    displayRowOfText(img,17,"p = choose next plate",(255,255,255))
    displayRowOfText(img,18,"file {}".format(basefilename),(255,255,255))
    if justSaved:
        sSaveStatus="(saved)"
    else:
        sSaveStatus="(updates not saved)"
    displayRowOfText(img,19,sSaveStatus,(255,255,255))    
        
    cv.imshow("statusWindow",img)

def nextGraphemeNumber():
    return (curGrapheme+1)%len(graphemes)

def computeViewPort(g):
    #g must be a grapheme, i.e. a list of component numbers
    #contours must already be defined
    ge=graphemeEdges(g,contours)
    print("Grapheme edges for g {} are {}".format(g,ge))
    midX=int((ge[0]+ge[1])/2)
    midY=int((ge[2]+ge[3])/2)
    halfSpan=max(midX-ge[0]+100,midY-ge[2]+100,600)
    print("Viewport is {}".format([midX-halfSpan,midX+halfSpan,midY-halfSpan,midY+halfSpan]))
    return [midX-halfSpan,midX+halfSpan,midY-halfSpan,midY+halfSpan]
    
def displayGrapheme(winname):
    displayInViewportLowRes(lowResLabels,graphemes[curGrapheme],graphemes[nextGraphemeNumber()],discarded,lowResFactor,winname)

def getRealCoordinates(x,y):
    #x,y are mouse coordinates -> translate into absolute coordinates on page (by taking viewport into account)
    f=getViewportFactor()
    return int(x*f+curViewPort[0]),int(y*f+curViewPort[2])

def performAction(listOfComponents,sAction):
    global curViewPort, justSaved
    print("Asked action {} on components {}".format(sAction,listOfComponents))
    if len(listOfComponents)>0:
        if sAction=="d": #discard selected components
            for l in listOfComponents:
                print("Working on {}".format(l))
                for g in graphemes:
                    if l in g:
                        print("l is in g, removing {} from {}".format(l,g))
                        g.remove(l)
                if not(l in discarded):
                    discarded.append(l)
        elif sAction=="t" or sAction=="n" or sAction=="c":    #attribute to current or next
            if sAction=="c":
                graphemes.insert(curGrapheme+1,[])
            if sAction=="t":
                nToAttributeTo=curGrapheme
            else:
                nToAttributeTo=nextGraphemeNumber()
            for l in listOfComponents:
                for idx, g in enumerate(graphemes):
                    if idx!=nToAttributeTo and l in g:
                        g.remove(l)
                if l in discarded:
                    discarded.remove(l)
                if not(l in graphemes[nToAttributeTo]):
                    graphemes[nToAttributeTo].append(l)
        cleanupEmptyGraphemes()
        justSaved=False
        updateStatusWindow()
        curViewPort=computeViewPort(graphemes[curGrapheme])
        displayGrapheme("main")
        


def cleanupEmptyGraphemes():
    global graphemes,curGrapheme
    graphemes=[g for g in graphemes if len(g)>0]
    if curGrapheme>=len(graphemes):
        curGrapheme=0

def selectComponents(event,x,y,flags,param):
   global ix,iy,drawing
   if event == cv.EVENT_LBUTTONDOWN:
       drawing = True
       ix,iy = x,y
   elif event == cv.EVENT_LBUTTONUP:
       (ixreal,iyreal)=getRealCoordinates(ix,iy)
       (xreal,yreal)=getRealCoordinates(x,y)
       if ixreal==xreal and iyreal==yreal:
           #if we just clicked, then find the closest component
           bestComponent=-1
           shortestDistance=9999999
           for c in list(range(1,numLabels)):
               br=cv.boundingRect(contours[c])
               bre=[br[0],br[0]+br[2],br[1],br[1]+br[3]]
               if haveIntersection(curViewPort,bre):
                   curDistance=-cv.pointPolygonTest(contours[c],(ixreal,iyreal),True)
                   if curDistance<shortestDistance:
                       bestComponent=c
                       shortestDistance=curDistance
           #print("Best component is {} with shortest distance {}".format(bestComponent,shortestDistance))
           if bestComponent>=0:
               performAction([bestComponent],curMode)
       else:
           #if we drew a rectangle, find all components that intersect with that rectangle
           ixreal,xreal=min(ixreal,xreal),max(ixreal,xreal)
           iyreal,yreal=min(iyreal,yreal),max(iyreal,yreal)
           thisRect=[ixreal,xreal,iyreal,yreal]
           selectedComponents=[]
           for c in list(range(1,numLabels)):
               br=cv.boundingRect(contours[c])
               bre=[br[0],br[0]+br[2],br[1],br[1]+br[3]]
               if haveIntersection(thisRect,bre):
                   selectedComponents.append(c)
           performAction(selectedComponents,curMode)

def saveCurrentPlate():
    global justSaved
    f=open(savefile,"wb")
    pickle.dump((curGrapheme,graphemes,discarded),f)
    f.close()
    platename=basefilename[:basefilename.rfind("_")]
    outputdirpath=os.path.join(outGraphemesDir,platename)
    #if dir already exists, remove it
    if os.path.isdir(outputdirpath):
        shutil.rmtree(outputdirpath)
    os.mkdir(outputdirpath)
    #now, save the graphemes themselves
    for idx, g in enumerate(graphemes):
        ge=graphemeEdges(g,contours)
        croppedMaskOfThisGrapheme = np.zeros((ge[3]-ge[2],ge[1]-ge[0]), dtype="uint8")
        for c in g:
            componentMaskCropped=((labels == c).astype("uint8") * 255)[ge[2]:ge[3],ge[0]:ge[1]]
            croppedMaskOfThisGrapheme = cv.bitwise_or(croppedMaskOfThisGrapheme, componentMaskCropped)
        baseOutFile=platename+"_"+str(idx)+"_"+str(int((ge[0]+ge[1])/2))+"_"+str(int((ge[2]+ge[3])/2))+"_"+str(ge[1]-ge[0])+"_"+str(ge[3]-ge[2])+".png"
        cv.imwrite(os.path.join(outputdirpath,baseOutFile),croppedMaskOfThisGrapheme)
    easygui.msgbox("Saved")
    justSaved=True


def loadCurrentPlate():
    global curGrapheme,graphemes,discarded,justSaved
    if os.path.exists(savefile):
        f=open(savefile,"rb")
        curGrapheme,graphemes,discarded=pickle.load(f)
        f.close()
    justSaved=True
        
    

#--------------------------------------
#   main function to segment graphemes
#---------------------------------------

def segmentGraphemes(nl,conts,slowMode,distanceCutOff):
    #pass the number of labels nl, the list of contours conts, slowMode if use real distance, and distanceCutOff in pixel
    #return graphemes = a list of list regrouping graphemes
    distances = getDistanceMatrix(nl,conts,slowMode)
    graphemes=[[i] for i in range(1,numLabels)]
    #at first, each component lives in its own cluster
    while True:
        hasRegrouped=False
        for g1 in graphemes:
            for g2 in graphemes:
                mustRegroup=False
                if not(g1==g2):
                    #print("Comparing graphemes {} with {}".format(g1,g2))
                    for c1 in g1:
                        for c2 in g2:
                            #print("Comparing components {} with {}".format(c1,c2))
                            if distances[c1,c2]<distanceCutOff:
                                mustRegroup=True
                                #print("Must be regrouped")
                if mustRegroup:
                    #print("Grouping graphemes {} and {}".format(g1,g2))
                    g1.extend(g2)
                    #print("Now grapheme g1 is ".format(g1))
                    #print("Now graphemes array is ".format(graphemes))
                    graphemes.remove(g2)
                    hasRegrouped=True
                    break
            if hasRegrouped:
                break
        if not(hasRegrouped):
            break
    return graphemes

def loadPlate(infile):
    global basefilename,cachefile,savefile,img,gray,numLabels,labels,contours,graphemes,lowResLabels,justSaved,discarded,curGrapheme
    basefilename=os.path.basename(infile)
    baseTifFilename=basefilename[:basefilename.rfind(".")]
    originalPlatePath=os.path.join(originalPlatesDir,baseTifFilename)
    print(originalPlatePath)
    #subprocess.run(['open', originalPlatePath], check=True, shell=True)
    subprocess.Popen(['start', originalPlatePath], shell=True)
    cachefile=os.path.join(cachedir,basefilename+".pkl")
    savefile=os.path.join(cachedir,basefilename+"_graphemesBinary.pkl")
    img=cv.imread(infile)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    numLabels,labels,contours = getComponentsAndContours(gray,cachefile)
    #graphemes will be a list of lists
    graphemes = segmentGraphemes(numLabels,contours,False,100)
    #compute a low-res version of labels to speed things up
    lowResLabels=cv.resize(labels.astype(np.float32),(int(labels.shape[1]/lowResFactor),int(labels.shape[0]/lowResFactor))).astype(np.int32)
    curGrapheme=0
    discarded=[]
    justSaved=False

def getNextUnprocessedFile():
    cachelist=os.listdir(cachedir)
    for d in os.listdir(indir):
        if not(d+"_graphemesBinary.pkl" in cachelist):
            break;
    return(os.path.join(indir,d))

#-------------------------------------------
# now main code starts
#-------------------------------------------------

originalPlatesDir=r"E:\personal\EtudesEgyptologie\DigitalResearch\P2_wimmer\inputData\Plates"
indir=r"E:\personal\EtudesEgyptologie\DigitalResearch\P2_wimmer\IntermediateData\CleanedUpImages"
cachedir=r"E:\personal\EtudesEgyptologie\DigitalResearch\P2_wimmer\IntermediateData\cache"
outGraphemesDir=r"E:\personal\EtudesEgyptologie\DigitalResearch\P2_wimmer\OutputData\graphemes"


prepareCache=False
if prepareCache:
    for r in os.listdir(indir):
        infile=os.path.join(indir,r)
        cachefile=os.path.join(cachedir,r+".pkl")
        img=cv.imread(infile)
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        print("files are {} and {}".format(infile,cachefile))
        getComponentsAndContours(gray,cachefile)
justSaved=False
discarded=[]
cv.namedWindow("statusWindow")
cv.namedWindow("main")
cv.setMouseCallback('main',selectComponents)
xsizeOfDisplayWindow= 800
curMode="t"
lowResFactor=4
curGrapheme=0
infile=getNextUnprocessedFile()
#infile=easygui.fileopenbox(msg="Cleaned up plate",default=indir+r"\*.png")
loadPlate(infile)



while (True):
    updateStatusWindow()
    curViewPort=computeViewPort(graphemes[curGrapheme])
    displayGrapheme("main")

    n=cv.waitKeyEx()
    #print("Key {}".format(n))
    if n==2555904:   #right arrow
        curGrapheme=nextGraphemeNumber()
    elif n==2424832:    #left arrow
        curGrapheme=(curGrapheme-1)%len(graphemes)
    elif n==ord("a"):
        performAction(graphemes[curGrapheme][:],"d")
    elif n==ord("t"):
        curMode="t"
    elif n==ord("d"):
        curMode="d"
    elif n==ord("n"):
        curMode="n"
    elif n==ord("c"):
        curMode="c"
    elif n==ord("l"):
        loadCurrentPlate()
    elif n==ord("s"):
        saveCurrentPlate()
    elif n==ord("q"):
        cv.destroyAllWindows()
        break
    elif n==ord("r"):
        infile=getNextUnprocessedFile()
        loadPlate(infile)
    elif n==ord("p"):
        infile=easygui.fileopenbox(msg="Cleaned up plate",default=indir+r"\*.png")
        loadPlate(infile)
        


        
        
    
