import json
import MySQLdb
import mysql.connector
import sensitive
import os
from lxml import etree

intermediateDataFolderPath = r'd:\hieraproject\P1_hieratable\intermediatedata'
spellingsPath = os.path.join(intermediateDataFolderPath,"ramses_spellings.json")
#frequenciesPath = os.path.join(intermediateDataFolderPath,"ramsesFrequenciesFull.json")
ramsesTextsFolderPath=os.path.join(intermediateDataFolderPath,"ramsesTexts")


#connect to database
ramsesdb = MySQLdb.connect("ramses.ulg.ac.be","phennebert",sensitive.ramsesPassword,"ramses",3306,charset="latin1")

#sSql = "SELECT document_id, substring(xmlcontent,53500,134) FROM db_text_tmp WHERE document_id=3919"
#sSql = "SELECT document_id, substring(xmlcontent,53634,1) FROM db_text_tmp WHERE document_id=3919"
#sSql = "SELECT document_id, replace(xmlcontent,char(194),'') FROM db_text_tmp WHERE document_id=3919"
#c=ramsesdb.cursor()
#c.execute(sSql)


if os.path.isfile(spellingsPath):
    spellings=json.load(open(spellingsPath))
    print("Loaded spellings from local json file")
else:
    #retrieve hashtable of spellings
    spellings={}
    sSql="SELECT spelling_id, MDC from spelling"
    c=ramsesdb.cursor()
    c.execute(sSql)
    for x in c.fetchall():
        print(str(x[0]) + " " + x[1])
        spellings[x[0]]=x[1]
    json.dump(spellings,open(spellingsPath,'w'))
    print("Loaded spellings from ramses db")

#now load all texts
allText=""
sAllTextPath=os.path.join(ramsesTextsFolderPath,"alltexts.txt")
if os.path.isfile(sAllTextPath):
    f=open(sAllTextPath,"r",encoding="utf-8")
    allText=f.read()
    f.close()
else:
    sSql = "SELECT text_id, replace(xmlcontent,char(194),'') FROM db_text_tmp WHERE document_id IN " + \
        " (SELECT document_id FROM document where datation_id in (SELECT thesaurus_id FROM thesaurus WHERE family_code='datation' AND " + \
        " ((order_code LIKE '.P5%' OR order_code LIKE '.P6.H21%' OR order_code LIKE '.P6.H22%' OR order_code LIKE '.P6.H23%'))) AND writing_system_id=3)" 
    c=ramsesdb.cursor()
    c.execute(sSql)

    for x in c.fetchall():
        sCurTextPath=os.path.join(ramsesTextsFolderPath,str(x[0])+".txt")
        if os.path.isfile(sCurTextPath):
            f=open(sCurTextPath,"r",encoding="utf-8")
            sCurText=f.read()
            f.close()
        else:
            sCurText = ""
            t = etree.fromstring(x[1])
            r=t.xpath("//word/spelling")
            for e in r:
                spelling = e.text
                if spelling in spellings:
                    sCurText+=spellings[spelling]+"\n"
            f=open(sCurTextPath,"w",encoding="utf-8")
            f.write(sCurText)
            f.close()
        print(x[0])
        allText+=sCurText+"-------\n"
    f=open(sAllTextPath,"w",encoding="utf-8")
    f.write(allText)
    f.close()

allText=allText.replace("\\det","")



def countInString(sFull,sMdc):
    #counts occurrences of mdc string sMdc in text sFull (trying to distinguish A1 from A11)
    mayBeBefore=["\\","&",":","\n","-","*"]
    mayBeAfter=["\\","&",":","\n","-","*"]
    c=0
    for b in mayBeBefore:
        for a in mayBeAfter:
            c+=sFull.count(b+sMdc+a)
    return c

#connect to hiera database
hieradb = mysql.connector.connect(
  host="localhost",
  user="root",
  password=sensitive.mysqlPassword,
  database="hiera"
)
#freq={}
sSql="SELECT id, mdc, jseshsyntax FROM signsandgroups"
c=hieradb.cursor()
c.execute(sSql)
for x in c.fetchall():
    n = countInString(allText,x[2])
    #freq[x[1]]=n
    c = hieradb.cursor()
    sql = "UPDATE signsandgroups SET ramsesFrequency=%s WHERE mdc=%s"
    val=(n,x[1])
    print(val)
    c.execute(sql,val)
    hieradb.commit()
    #if n==0:
        #print(x[1])
        #print("{},{},{}".format(x[0],x[1],x[2]))
#json.dump(freq,open(frequenciesPath,'w'))

