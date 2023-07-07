import os
import subprocess
import pathlib
import mysql.connector
import re, string
import cv2 as cv

patternOnlyAlphanum = re.compile('[\W_]+')

rootdir=r"c:\hieraproject"
outHierogSvgDir=os.path.join(rootdir,"P2_wimmer","OutputData","wimmerHierog")
intermediateHierogPNGDir=os.path.join(rootdir,"P2_wimmer","IntermediateData","svgHierogPNG")
intermediateHierogBMPDir=os.path.join(rootdir,"P2_wimmer","IntermediateData","svgHierogBMP")
potracePath=os.path.join(rootdir,r"OutilsOpenSource\potrace\potrace.exe")
mdcToPngFolder=os.path.join(rootdir,"OutilsOpenSource","JSeshCustom")
mdcToPngJar="mdctobitmap.jar"
mdcToPngLibFolder=os.path.join(mdcToPngFolder,"lib")
def mdctopng(sMdc,fPng):
    arr=["java","-cp",os.path.join(mdcToPngLibFolder,"*"),"-jar",os.path.join(mdcToPngFolder,mdcToPngJar),sMdc,fPng]
    print(' '.join(arr))
    process=subprocess.Popen(arr,subprocess.CREATE_NO_WINDOW)
    process.wait()


#connect to database
hieradb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="pTurin1880!",
  database="hiera"
)

missingMDC={}
c=hieradb.cursor()
c.execute("SELECT mdc,jseshsyntax,id FROM signsandgroups where svgpath is null")
for x in c.fetchall():
    missingMDC[x[0]]={"jseshsyntax":x[1],"id":x[2]}
c.close()

for k,v in missingMDC.items():
    sMDC = missingMDC[k]
    sJsesh= v["jseshsyntax"]
    outFileName=patternOnlyAlphanum.sub('', k)+"_"+str(v["id"])
    sPNGpath=os.path.join(intermediateHierogPNGDir,outFileName+"_hierog.png")
    if not(os.path.isfile(sPNGpath)):
        mdctopng(sJsesh,sPNGpath)
    sBMPPath=os.path.join(intermediateHierogBMPDir,outFileName+"_hierog.bmp")
    img=cv.imread(sPNGpath)
    cv.imwrite(sBMPPath,img)
    sSVGPath=os.path.join(outHierogSvgDir,outFileName+"_hierog.svg")
    process=subprocess.Popen([potracePath,sBMPPath,"-o",sSVGPath,"-s","--scale","0.06"],creationflags=subprocess.CREATE_NO_WINDOW)
    process.wait()
    sql = "UPDATE signsandgroups set svgpath='"+sSVGPath.replace("\\","\\\\")+"' WHERE id="+str(v["id"])
    c = hieradb.cursor()
    c.execute(sql)
    hieradb.commit()    
    print(sql)
    
