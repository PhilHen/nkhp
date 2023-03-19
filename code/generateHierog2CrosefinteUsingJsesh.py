import os
import subprocess
import pathlib

rootdir=r"c:\hieraproject"
gardinermollerCorrespFile=os.path.join(rootdir,"P1_hieratable","IntermediateData","GardinerMoller.txt")
crosefinteMetadataFile=os.path.join(rootdir,"P1_hieratable","IntermediateData","crosefintemetadata.txt")
crosefinteimgdir=os.path.join(rootdir,"P1_hieratable","IntermediateData","pdfextract","img")

mdcToPngFolder=os.path.join(rootdir,"OutilsOpenSource","JSeshCustom")
mdcToPngJar="mdctobitmap.jar"
mdcToPngLibFolder=os.path.join(mdcToPngFolder,"lib")

def mdctopng(sMdc,fPng):
    arr=["java","-cp",os.path.join(mdcToPngLibFolder,"*"),"-jar",os.path.join(mdcToPngFolder,mdcToPngJar),sMdc,fPng]
    print(' '.join(arr))
    process=subprocess.Popen(arr,subprocess.CREATE_NO_WINDOW)
    process.wait()

#on crée le dict de correspondance Gardiner-JSesh (spatialisation des groupes)
gardiJsesh={}
fmatch=open(gardinermollerCorrespFile,encoding='utf-8')
matchrows=(line.split('\t') for line in fmatch)
for r in matchrows:
    gardiJsesh[r[0]]=r[4]
fmatch.close()

#puis on crée le dict de correspondance crosefinte-hiera-id to gardi
croseFinteHieraIdToGardi={}
fmatch=open(crosefinteMetadataFile,encoding='utf-8')
matchrows=(line.split('\t') for line in fmatch)
for r in matchrows:
    croseFinteHieraIdToGardi[r[3][:-1]]=r[0]
fmatch.close()

#now create hierog2 png images
for k,v in croseFinteHieraIdToGardi.items():
    sMDC = gardiJsesh[v]
    sPNGpath=os.path.join(crosefinteimgdir,k+"_hierog2.png")
    if not(os.path.isfile(sPNGpath)):
        mdctopng(sMDC,sPNGpath)
        print("{} is {}".format(k,sMDC))
    

