import os
import subprocess
import cv2 as cv
import pathlib

rootdir=r"c:\hieraproject"
inputdir=os.path.join(rootdir,"P1_hieratable","IntermediateData","pdfextract","img")
intermediatedir=os.path.join(rootdir,"P1_hieratable","IntermediateData","pdfextract","imgBmp")
outputdir=os.path.join(rootdir,"P1_hieratable","IntermediateData","pdfextract","imgsvg")
potracePath=os.path.join(rootdir,r"OutilsOpenSource\potrace\potrace.exe")

k=cv.getStructuringElement(cv.MORPH_ELLIPSE,(2,2))
for f in os.listdir(inputdir):
    stem=pathlib.Path(f).stem
    if pathlib.Path(f).suffix==".png" and not(stem.endswith("hierog")): #on n'utilise que les hierog2 (générés par JSesh)
        fullInputPath=os.path.join(inputdir,f)
        print(f)
        fullBMPPath=os.path.join(intermediatedir,pathlib.Path(f).stem+".bmp")
        fullSVGPath=os.path.join(outputdir,pathlib.Path(f).stem+".svg")
        img=cv.imread(fullInputPath)
        #img3=cv.morphologyEx(img,cv.MORPH_OPEN,k)
        cv.imwrite(fullBMPPath,img)
        process=subprocess.Popen([potracePath,fullBMPPath,"-o",fullSVGPath,"-s","--scale","0.06"],creationflags=subprocess.CREATE_NO_WINDOW)
        #print(" ".join([potracePath,fullBMPPath,"-o",fullSVGPath,"-s","--scale","0.06"]))
        process.wait()
