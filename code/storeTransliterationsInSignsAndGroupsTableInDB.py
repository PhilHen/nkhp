import json
import mysql.connector
import sensitive
import mdc2unicode

# on crée d'abord un tableau des translitérations
from lxml import etree
from io import StringIO, BytesIO  
tree=etree.parse(r'd:\hieraproject\P1_hieratable\InputData\signs_description.xml') 
r=tree.xpath('//hasTransliteration')
transliterations={}
for e in r:
 sign=e.attrib['sign']
 trans=e.attrib['transliteration']
 type=e.attrib['type']
 if not sign in transliterations:
  transliterations[sign]={}
 if not type in transliterations[sign]:
  transliterations[sign][type]=[]
 transliterations[sign][type].append({'ascii' : trans, 'unicode': unicodeTransliteration(trans)});

#connect to database
hieradb = mysql.connector.connect(
  host="localhost",
  user="root",
  password=sensitive.mysqlPassword,
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

mdcIds=loadSqlToDict("SELECT mdc,id FROM hiera.signsandgroups")
for k,v in mdcIds.items():
    if k in transliterations:
        jsonDump = json.dumps(transliterations[k])
        c = hieradb.cursor()
        sql = "UPDATE signsandgroups SET alltransliterations = %s WHERE id = %s"
        val = (jsonDump,mdcIds[k])
        c.execute(sql, val)
        hieradb.commit()
        print(sql)
