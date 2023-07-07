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

metatypeidFromName=loadSqlToDict("SELECT name,id from hiera.metadatatypes")
sourceidFromCode=loadSqlToDict("SELECT name,id from hiera.sources")
wimmerPlateToMDC = loadSqlToDict("select wimmerplateid, mdc from signsandgroups SG1 where wimmerplateid is not null " + \
                                "and 1=(select count(*) from signsandgroups SG2 where SG1.wimmerplateid=SG2.wimmerplateid)")
periodByGrapheme={}
periodFile=os.path.join(rootdir,"P2_wimmer","IntermediateData","graphemesByPeriod.txt")
fmatch=open(periodFile,encoding='utf-8')
matchrows=(line.split('\t') for line in fmatch)
for r in matchrows:
    periodByGrapheme[r[0]]=r[1][:-1]


#puis on parcourt les svg de C:\hieraProject\P2_wimmer\OutputData\graphemes
# pour chacun, il faut trouver le hiéroglyphe et la période. Si on n'a pas le hiéroglyphe, on met "???" pour les retrouver aisément
dirGraphemes=os.path.join(rootdir,"P2_wimmer","OutputData","graphemes")
svgfiles=os.listdir(dirGraphemes)
nSourceIdWimmer=sourceidFromCode["Wimmer"]
for f in svgfiles:
    if f[-4:]=='.svg':
        hiera_id=f[:-4]
        print("Processing " + hiera_id)
        period=periodByGrapheme[hiera_id]
        plateid="_".join(f.split("_")[0:3])
        mdc="???"
        if plateid in wimmerPlateToMDC:
            mdc=wimmerPlateToMDC[plateid]
        sql="INSERT INTO hiera.graphemes (name, source_id) values (%s, %s)"
        val=(hiera_id,nSourceIdWimmer)
        c=hieradb.cursor()
        c.execute(sql,val)
        c.close()
        hieradb.commit()
        #now retrieve the id of the sign just saved
        x = retrieveValuesFromDb("SELECT id from hiera.graphemes where name='"+hiera_id+"' AND source_id="+str(nSourceIdWimmer))
        signId=x[0]
        print(signId)
        #now save to db
        sql = "INSERT INTO hiera.graphemesmetadata (metadatatype_id, value,grapheme_id) values (%s, %s, %s)"
        vals=[(metatypeidFromName['MDC'],mdc,signId),(metatypeidFromName['date'],period,signId),\
          (metatypeidFromName['path'],os.path.join(dirGraphemes,f),signId), \
          (metatypeidFromName['wimmerPlate'],plateid,signId), \
          (metatypeidFromName['facsimileCreatedBy'],'Stefan Wimmer',signId]
        c=hieradb.cursor()
        c.executemany(sql,vals)
        hieradb.commit()



