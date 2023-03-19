import os
import json
import shutil
import mysql.connector

rootdir=r"c:\hieraproject"

#connect to database
hieradb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="pTurin1880!",
  database="hiera"
)


def loadSqlToDict(sSql):
    d={}
    c=hieradb.cursor()
    c.execute(sSql)
    for x in c.fetchall():
        d[x[0]]=x[1]
    c.close()
    return d

def retrieveValuesFromDb(sSql):
    d={}
    c=hieradb.cursor()
    c.execute(sSql)
    x=c.fetchone()
    c.close()
    return x

#get translations for AKU
akutranslations=loadSqlToDict("SELECT fromText,toText FROM hiera.translations where context='AKUMetadata'")
metatypeidFromName=loadSqlToDict("SELECT name,id from hiera.metadatatypes")
sourceidFromCode=loadSqlToDict("SELECT name,id from hiera.sources")

#on charge la correspondance Gardiner-Möller (future table mysql SignsAndGroups)
gardinermollerCorrespFile=os.path.join(rootdir,"P1_hieratable","IntermediateData","GardinerMoller.txt")
gardimoll={}
fmatch=open(gardinermollerCorrespFile,encoding='utf-8')
matchrows=(line.split('\t') for line in fmatch)
for r in matchrows:
    gardimoll[r[0]]={"MDC": r[0]}
    if r[1]!="" and r[2]!="":
        sMoll=r[1]+"="+r[2]
    else:
        sMoll=r[1]+r[2]
    gardimoll[r[0]]['Möller']=sMoll
    if r[3]!="":
        gardimoll[r[0]]['WimmerPlate']=r[3]
    gardimoll[r[0]]['JSesh']=r[4]
    #print(gardimoll[r[0]])
fmatch.close()

dirimgpdf=os.path.join(rootdir,"P1_hieratable","IntermediateData","pdfextract","imgsvg")

crosefinteMetadataFile=os.path.join(rootdir,"P1_hieratable","IntermediateData","crosefintemetadata.txt")
fmatch=open(crosefinteMetadataFile,encoding='utf-8')
matchrows=(line.split('\t') for line in fmatch)
for r in matchrows:
    hiera_id=r[3][:-1]
    print("Processing " + hiera_id)
    nSourceIdCrosefinte=sourceidFromCode["Crosefinte"]
    sql="INSERT INTO hiera.graphemes (name, source_id) values (%s, %s)"
    val=(hiera_id,nSourceIdCrosefinte)
    c=hieradb.cursor()
    c.execute(sql,val)
    c.close()
    hieradb.commit()
    #now retrieve the id of the sign just saved
    x = retrieveValuesFromDb("SELECT id from hiera.graphemes where name='"+hiera_id+"' AND source_id="+str(nSourceIdCrosefinte))
    signId=x[0]
    print(signId)
    #now save to db
    sql = "INSERT INTO hiera.graphemesmetadata (metadatatype_id, value,grapheme_id) values (%s, %s, %s)"
    vals=[(metatypeidFromName['MDC'],r[0],signId),(metatypeidFromName['text'],r[1],signId),\
          (metatypeidFromName['path'],os.path.join(dirimgpdf,hiera_id+'_hierat.svg'),signId)]
    c=hieradb.cursor()
    c.executemany(sql,vals)
    hieradb.commit()
fmatch.close()



