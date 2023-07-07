import os
import subprocess
import cv2 as cv
import pathlib

rootdir=r"c:\hieraproject"
inputdir=os.path.join(rootdir,r"P2_wimmer\IntermediateData\graphemes")
intermediatedir=os.path.join(rootdir,r"P2_wimmer\IntermediateData\processedGraphemes")
outputdir=os.path.join(rootdir,r"P2_wimmer\outputData\graphemes")
potracePath=os.path.join(rootdir,r"OutilsOpenSource\potrace\potrace.exe")
imageMagickPath=r"C:\Program Files\ImageMagick-7.1.0-Q16-HDRI\magick.exe"

k=cv.getStructuringElement(cv.MORPH_ELLIPSE,(5,5))
for dd in os.listdir(inputdir):
    print(dd)
    for f in os.listdir(os.path.join(inputdir,dd)):
        if pathlib.Path(f).suffix==".png":
            fullInputPath=os.path.join(inputdir,dd,f)
            stem=pathlib.Path(f).stem
            fullBMPPath=os.path.join(intermediatedir,pathlib.Path(f).stem+".bmp")
            fullSVGPath=os.path.join(outputdir,pathlib.Path(f).stem+".svg")
            fullReRasterPath=os.path.join(outputdir,pathlib.Path(f).stem+".png")
            img=cv.imread(fullInputPath)
            img2=cv.bitwise_not(img)
            img3=cv.morphologyEx(img2,cv.MORPH_OPEN,k)
            cv.imwrite(fullBMPPath,img3)
            process=subprocess.Popen([potracePath,fullBMPPath,"-o",fullSVGPath,"-s","--scale","0.06"],creationflags=subprocess.CREATE_NO_WINDOW)
            process.wait()
            process=subprocess.Popen([imageMagickPath,fullSVGPath,fullReRasterPath],creationflags=subprocess.CREATE_NO_WINDOW)
            
            

