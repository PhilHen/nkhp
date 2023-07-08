import json
import mysql.connector
import sensitive
import mdc2unicode

# load transliterations from csv into dictionary dictTranslit
translitcsv=r"D:\hieraProject\P1_hieratable\IntermediateData\hierogtranslit.csv"
ftranslit=open(translitcsv,encoding='utf-8-sig')
translitrows=(line.split('\t') for line in ftranslit)
dictTranslit={}
for r in translitrows:
    sMultipleTranslits=r[1][0:-1]
    if sMultipleTranslits=="-":
        sMultipleTranslits=""
    if sMultipleTranslits!="":
        dictTranslit[r[0]]=[]
        for sTranslit in sMultipleTranslits.split(","):
            dictTranslit[r[0]].append({'ascii':mdc2unicode.unicode2mdc(sTranslit),'unicode':sTranslit})
ftranslit.close()


#connect to database
hieradb = mysql.connector.connect(
  host="localhost",
  user="root",
  password=sensitive.mysqlPassword,
  database="hiera"
)

for k,v in dictTranslit.items():
    jsonDump=json.dumps(dictTranslit[k])
    print(jsonDump)
    c = hieradb.cursor()
    sql = "UPDATE signsandgroups SET transliterations = %s WHERE mdc = %s"
    val = (jsonDump,k)
    c.execute(sql, val)
    hieradb.commit()
