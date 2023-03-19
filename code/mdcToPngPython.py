import os
import subprocess
import pathlib

rootdir=r"c:\hieraproject"
mdcToPngFolder=os.path.join(rootdir,"OutilsOpenSource","JSeshCustom")
mdcToPngJar="mdctobitmap.jar"
mdcToPngLibFolder=os.path.join(mdcToPngFolder,"lib")

def mdctopng(sMdc,fPng):
    arr=["java","-cp",os.path.join(mdcToPngLibFolder,"*"),"-jar",os.path.join(mdcToPngFolder,mdcToPngJar),sMdc,fPng]
    print(' '.join(arr))
    process=subprocess.Popen(arr,subprocess.CREATE_NO_WINDOW)
    process.wait()
    

mdctopng("A1-Y1",r"c:\mystuff.png")
