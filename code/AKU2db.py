import os
import json
import shutil
import mysql.connector

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

#insert multiple rows using https://www.w3schools.com/python/python_mysql_insert.asp

dirtxt=r'c:\hieraproject\P1_hieratable\IntermediateData\AKUscrapingResults\txt'
dirsvg=r'c:\hieraproject\P1_hieratable\IntermediateData\AKUscrapingResults\svg'
txtfiles=os.listdir(dirtxt)
for txtfile in txtfiles:
 if txtfile[-4:]=='.txt':
  hiera_id=txtfile[:-4]
  print("Processing " + hiera_id)

  #save sign in SIGNS table
  nSourceIdAKU=sourceidFromCode["AKU"]
  sql="INSERT INTO hiera.graphemes (name, source_id) values (%s, %s)"
  val=(hiera_id,nSourceIdAKU)
  c=hieradb.cursor()
  c.execute(sql,val)
  c.close()
  hieradb.commit()
  #now retrieve the id of the sign just saved
  x = retrieveValuesFromDb("SELECT id from hiera.graphemes where name='"+hiera_id+"' AND source_id="+str(nSourceIdAKU))
  signId=x[0]
  print(signId)
  
  fin=open(dirtxt+'\\'+txtfile,encoding='utf-8')
  rows = ( line.split('\t') for line in fin )
  d = { row[0]:row[1][:-1] for row in rows }
  if d['Textinhalt'].startswith("Textart:"):
   d['Textinhalt']=d['Textinhalt'][8:].lstrip()
  #now save to db
  sql = "INSERT INTO hiera.graphemesmetadata (value, metadatatype_id,grapheme_id) values (%s, %s, %s)"
  vals=[]
  for k,v in d.items():
      vals.append((v[0:400],metatypeidFromName[akutranslations[k]],signId))
  pathHierat=os.path.join(dirsvg,hiera_id+"_hierat.svg")
  vals.append((pathHierat,metatypeidFromName["path"],signId))
  c=hieradb.cursor()
  c.executemany(sql,vals)
  hieradb.commit()

