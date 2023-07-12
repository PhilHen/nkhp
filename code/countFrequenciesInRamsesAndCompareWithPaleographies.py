import json
import MySQLdb
import mysql.connector
import sensitive
import os
from lxml import etree

#first, extract spellings and texts from the Ramses database
intermediateDataFolderPath = r'd:\hieraproject\P1_hieratable\intermediatedata'
spellingsPath = os.path.join(intermediateDataFolderPath,"ramses_spellings.json")
ramsesTextsFolderPath=os.path.join(intermediateDataFolderPath,"ramsesTexts")
absentSignsPath=os.path.join(intermediateDataFolderPath,"signsInRamsesButNotInPaleographies.csv")

#connect to database
ramsesdb = MySQLdb.connect("ramses.ulg.ac.be","phennebert",sensitive.ramsesPassword,"ramses",3306,charset="latin1")

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

allTextDegenerate=allText.replace("\\det","").replace("*","/").replace(":","/").replace("\r\n","/").replace("-","/").\
                    replace("\n","/").replace("&","/").replace("_","/").replace("(","/").replace(")","/").replace("^","/").\
                    replace("=","/").replace("[","/").replace("]","/").replace("?","/").replace("!","/")

while True:
    allTextDegenerate=allTextDegenerate.replace("//","/")
    cn = allTextDegenerate.count("//")
    if cn==0:
        break
allSigns = allTextDegenerate.split("/")

def cleanupSign(s):
    s=s.split("#")[0]
    s=s.split("{{")[0]
    s=s.split("\\")[0]
    if s=="nn":
        s="M22+M22"
    if s in ["shading1234","{","}","o","R","0>","<1","<0","2>","..",".","v","h","nTrw","<",">","1>","'","O","$r","$b","n","<2","\""] or s.isdigit():
        s=""
    return s

allSigns=[cleanupSign(s) for s in allSigns if cleanupSign(s)!=""]
signs = {}
for s in allSigns:
    if s in signs:
        signs[s]["freq"]=signs[s]["freq"]+1
    else:
        signs[s]={"sign":s,"freq":1}
signs=dict(sorted(signs.items(),key= lambda item: item[1]["freq"], reverse=True))


#now only keep those absent that are not present (with at least one occurrence) in hiera database
hieradb = mysql.connector.connect(
  host="localhost",
  user="root",
  password=sensitive.mysqlPassword,
  database="hiera"
)

sSql="SELECT mdc FROM signsandgroups WHERE ramsesFrequency>0"
c=hieradb.cursor()
c.execute(sSql)
for x in c.fetchall():
    if x[0] in signs:
        del signs[x[0]]
    #signsAttested.append(x[0])
c.close()

f=open(absentSignsPath,"w",encoding="utf-8")
for k,v in signs.items():
    f.write(k+","+str(v["freq"])+"\n")
f.close()

print("Finished, saved {} signs".format(len(signs)))

