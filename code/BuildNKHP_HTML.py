import os
import base64
import json
import shutil
import mysql.connector
import re, string
import json
import sensitive


htmlTemplateFile=r"D:\hieraProject\P1_hieratable\Code\htmltemplate.htm"
rootdir=r"d:\hieraproject"
dstwebserverfolder=r"d:\hieratable"
#generateCSVextract=True
generateCSVextract=False
csvExtractImgFolder=os.path.join(rootdir,"P1_hieratable","IntermediateData","extractForTranslitDir")
csvExtractFilePath=os.path.join(rootdir,"P1_hieratable","IntermediateData","extractForTranslit.csv")
outhtmlpath=os.path.join(dstwebserverfolder,"hieratest.htm")

#load html template
f = open(htmlTemplateFile,"r",encoding="utf-8")
sHtml = f.read()
f.close()

#connect to database
hieradb = mysql.connector.connect(
  host="localhost",
  user="root",
  password=sensitive.mysqlPassword,
  database="hiera"
)

#destination image folder (for web server)
dstimgfolder=os.path.join(dstwebserverfolder,"img")

#on crée le tableau des catégories de texte
dcat={}
sSql="SELECT akuDescription, internalCateg from TextCateg"
c = hieradb.cursor()
c.execute(sSql)
for x in c.fetchall():
    dcat[x[0]]="C"+x[1]

# on charge depuis la db le tableau des signes hiéroglyphiques - il faut cependant copier encore les hiéroglyphes eux-mêmes
patternOnlyAlphanum = re.compile('[\W_]+')
signsDict={}
sSql="SELECT mdc, svgpath, if(singleMoellerCodes is null,'',singleMoellerCodes),if(groupMoellerCode is null, '',groupMoellerCode),id, " + \
          " if(transliterations is null, '', transliterations) FROM signsAndGroups"
#on n'inclut pas encore les translitérations ici
c=hieradb.cursor()
c.execute(sSql)
for x in c.fetchall():
    mdc=x[0]
    mdconlyalphanum=patternOnlyAlphanum.sub('', mdc)
    if x[2]!="" and x[3]!="":   #codes Möller
        sMoll=x[2]+"="+x[3]
    else:
        sMoll=x[2]+x[3]
    sInputPath=x[1]
    sHierogOutputFilename="g"+str(x[4])+".svg"
    shutil.copy(sInputPath,os.path.join(dstimgfolder,sHierogOutputFilename))
    signsDict[mdc]={"gardi":x[0],"hierog":sHierogOutputFilename,"N Möller":sMoll}
    if x[5]!="":
        signsDict[mdc]["translit"]=json.loads(x[5])
    if mdconlyalphanum!=mdc:
        signsDict[mdc]['ligature']="lig"
c.close()



#load rawHieratogramdata (i.e. all hieratogram metadata) from mysql database
rawHieratogramdata={}
sSql = "select graphemes.name, M1.name, G1.value, sources.name  from graphemes, metadatatypes M1,graphemesmetadata G1,sources " + \
     "where G1.grapheme_id=graphemes.id and G1.metadatatype_id=M1.id and sources.id=graphemes.source_id " + \
     "and (sources.name='Crosefinte' or sources.name='Wimmer' or (sources.name='AKU' " + \
     "and exists(select 1 from graphemesmetadata G2, metadatatypes M2 where G1.grapheme_id=G2.grapheme_id and G2.metadatatype_id=M2.id " + \
     "and M2.name='date' and (G2.value like 'Dritte Zwischenzeit%' or G2.value like 'Neues%')))) " + \
    " order by graphemes.name, M1.name"
c=hieradb.cursor()
c.execute(sSql)
for x in c.fetchall():
    if not(x[0] in rawHieratogramdata):
        rawHieratogramdata[x[0]]={'id':x[0], 'extractedFrom':x[3]}
    sx2 = x[2]
    if x[1]=="wimmerPlate":
        sx2=sx2.split("_")[2]
    rawHieratogramdata[x[0]][x[1]]=sx2
c.close()

datatoadd=[]
for k,d in rawHieratogramdata.items():
    hiera_id=d['id']
    sHieratOutputFileName="h"+str(hiera_id)+".svg"    #hiératogramme h1234.svg par exemple
    shutil.copy(d['path'],os.path.join(dstimgfolder,sHieratOutputFileName))
    datatoadd.append(d)
    if len(d) % 100 ==0:
        print("Processing " + hiera_id)

def getmdcnormalized(d):
  s=d['MDC']
  #olds=s
  suffix=""
  prefix=""
  category="0"  #pour mettre les signes devant et ligatures à la fin
  if d['extractedFrom']=='Crosefinte':
    category="1"
  if not s[-1].isdigit():
   suffix=s[-1]
   s=s[:-1]
  if s.startswith('Aa'):
   prefix="ZZ"
   s=s[2:]
  else:
   prefix=s[0]
   s=s[1:]
  if len(s)==1:
   s="00"+s
  elif len(s)==2:
   s="0"+s
  #print("was " + olds + " , is now " + prefix + s + suffix)
  return category+prefix+s+suffix

datatoadd.sort(key=getmdcnormalized)

def getOrderString(b):
  #b sera un élément de signsDict
  s=b["gardi"]
  suffix=""
  prefix=""
  category="1" if "ligature" in b else "0"
  if not s[-1].isdigit():
   suffix=s[-1]
   s=s[:-1]
  if s.startswith('Aa'):
   prefix="ZZ"
   s=s[2:]
  else:
   prefix=s[0]
   s=s[1:]
  if len(s)==1:
   s="00"+s
  elif len(s)==2:
   s="0"+s
  return category+prefix+s+suffix


#on essaie de regrouper par signe Gardiner, et d'assigner aux différentes colonnes

#les nouvelles colonnes seront
column_headers = {
    0: "18D",
    1: "18D <= Th III",
    2: "18D > Th III",
    3: "19D",
    4: "20D",
    5: "21-22-23D"
}

column_möllersources_mappings = {
    'Louvre 3226' : 1,
    'Berlin 3029' : 2,
    'Gurob' : 2,
    'Rollin' : 3,
    'Inena' : 3,
    'Pentaour': 3,
    'Harris Th.': 4,
    'Harris H.M.': 4,
    'Abbott' : 4,
    'nDm.t' : 5
}

def compute_column(d):  #d is a hieratogram_data
    col=-1
    if 'date' in d:
        if d['date'].startswith('Dritte Zwischen'):
            col=5
        elif d['date'].startswith('Neues Reich, 18. Dynastie, Amenhotep I.') \
            or d['date'].startswith('Neues Reich, 18. Dynastie, Hatschepsut') \
            or d['date'].startswith('Neues Reich, 18. Dynastie, Thutmosis III.') :
            col=1
        elif d['date'].startswith('Neues Reich, 18. Dynastie, Amenhotep II.') \
            or d['date'].startswith('Neues Reich, 18. Dynastie, Amenhotep IV.') \
            or d['date'].startswith('Neues Reich, 18. Dynastie, Amenhotep III.') \
            or d['date'].startswith('Neues Reich, 18. Dynastie, Tutanchamun'):
            col=2
        elif d['date'].startswith('Neues Reich, 18. Dynastie'):
            col=0
        elif d['date'].startswith('Neues Reich, 19. Dynastie'):
            col=3
        elif d['date'].startswith('Neues Reich, 20. Dynastie'):
            col =4
        elif d['date'] in ['Amenmnesse', 'Merneptah', 'Ramses II (1-25)', 'Ramses II (26-45)', 'Ramses II (46-67)','Sethos I', 'Sethos II','Siptah/Tawosret']:
            col=3   #19D
        elif d['date'] in ['Ramses III (1-11)', 'Ramses III (12-21)','Ramses III (22-32)','Ramses IV','Ramses IX','Ramses V','Ramses VI','Ramses VII','Sethnachte']:
            col=4   #20D
    if 'text' in d:
        if d['text'] in column_möllersources_mappings:
            col=column_möllersources_mappings[d['text']]
    return col

for d in datatoadd:
 mdc=d['MDC']
 d['html_column']=compute_column(d)
 if mdc in signsDict:
  if not("hieratogram_data" in signsDict[mdc]):
   signsDict[mdc]['hieratogram_data']=[]
  signsDict[mdc]['hieratogram_data'].append(d)
 else:
  print("Abnormal: could not find {}, {} in signsDict".format(mdc,d['extractedFrom']))
 if d['extractedFrom']=='Crosefinte':
   #print(mdc + " is ligature")
   signsDict[mdc]['ligature']="lig"
  #elif d['extractedFrom']=='AKU':
  #  signsDict[mdc]['N Möller']=d['N Möller']

#maintenant, on supprime tous les éléments dans signsDict qui n'ont pas de hiératogramme
print("Before removal: {} element".format(len(signsDict)))
arr=[]
for k,v in signsDict.items():
    if not("hieratogram_data" in v):
        arr.append(k)
for k in arr:
    del signsDict[k]
print("After removal: {} element".format(len(signsDict)))

#Pour chaque code Gardiner, on va trier les hiératogrammes par registre (catégorie) de texte
print("Début du tri par registre de texte")
for gardikey in signsDict:
 b=signsDict[gardikey]
 for hd in b['hieratogram_data']:
    #hd['registreCateg']=dcat[hd["textContentType"]] if (hd['extractedFrom']=='AKU' and hd["textContentType"] in dcat) else "C99-OTH"
    hd['registreCateg']=dcat[hd["textContentType"]] if ("textContentType" in hd and hd["textContentType"] in dcat) else "C99-OTH"
 b['hieratogram_data']=sorted(b['hieratogram_data'], key=lambda x:x['registreCateg'])
print("fin du tri")

categDescrip= { \
"C01-LITT" : {"fr":"littéraire", "en":"literary","color":"D98880"},\
"C02-DOC" : {"fr":"documentaire", "en":"documentary","color":"C39BD3"},\
"C03-RELIG" : {"fr":"religieux","en":"religious","color":"7FB3D5"}, \
"C04-MM" : {"fr":"médico-magique","en":"medical/magical","color":"76D7C4"}, \
"C05-ROY" : {"fr":"royal","en":"royal","color":"F7DC6F"},\
"C06-JUR" : {"fr":"juridique","en":"judicial","color":"D6DBDF"},\
"C07-BES" : {"fr":"besuchertexte","en":"besuchertexte","color":"AED6F1"},\
"C98-UNK" : {"fr":"inconnu","en":"unknown","color":"F4F6F6"}, \
"C99-OTH" : {"fr":"autres","en":"other","color":"F4F6F6"} \
}

#Template CSS pour les types de textes
s1=""
s2=""
for cdk in categDescrip.keys():
    bkg=" {background:#"+categDescrip[cdk]["color"]+ "}"
    s1+="."+cdk+bkg+"\n"
    s2+=".checkboxfor"+cdk+bkg+"\n"
sHtml=sHtml.replace("XXXTEXTREGISTRIESCSSXXX",s1+s2)

#Checkboxes pour les types de textes, et initialisation de la variable javascript contenant les différents codes de types de textes
s=""
for c in sorted(set(dcat.values())):
  s+="<td class='checkboxfor"+c+"'><input type='checkbox' onchange='changeCategClassVisibilities()' id='check_cat"+c+"' checked><span class='fr_lang'>"+categDescrip[c]["fr"]+"</span><span class='en_lang'>"+categDescrip[c]["en"]+"</span></td>"
sHtml=sHtml.replace("XXXTDFORTEXTCATEGXXX",s)
sHtml=sHtml.replace("XXXSCRIPTFORTEXTCATEGCLASSESXXX","sCategClasses='"+"/".join(sorted(set(dcat.values())))+"'")

sHtHgVariables="hg={"
isFirst=True
for gardikey in signsDict:
 if not(isFirst):
     sHtHgVariables+=",\n"
 isFirst=False
 b=signsDict[gardikey]
 sHtHgVariables+="'"+gardikey.replace("\\","\\\\") + "': '"+ b['hierog'] + "'"
sHtHgVariables+="};\nht={"
isFirst=True
for gardikey in signsDict:
  b=signsDict[gardikey]
  for hd in b["hieratogram_data"]:
    if not(isFirst):
        sHtHgVariables+=",\n"
    isFirst=False
    sHtHgVariables+="'"+hd['id']+"':'"+gardikey.replace("\\","\\\\")+"'"
sHtHgVariables+="}\n"
sHtml=sHtml.replace("XXXHTHGOBJECTSXXX",sHtHgVariables)

sTableContent='<thead><tr>'
sTableContent+='<th>Gardiner</th>'
sTableContent+='<th>Möller</th>'
sTableContent+='<th>Hieroglyphe</th>'
sTableContent+='<th>Translit</th>'
sTableContent+='<th><center>n (Rams)</center></th>'
for ch in column_headers:
 sTableContent+="<th><center>"+column_headers[ch]+"</center></th>"
sTableContent+="<th>order</th>"
sTableContent+="<th>translit mdc</th>"
sTableContent+='</tr></thead><tbody>'


jsontxtfile=os.path.join(rootdir,"P1_hieratable","IntermediateData","ramsesfrequencies.json")
frequencies=json.load(open(jsontxtfile))
csvlines=[]
for gardikey in signsDict:
 b=signsDict[gardikey]
 #print("Adding all for " + b["gardi"]);
 sCurCSVLine=b["gardi"]
 if generateCSVextract:
     sCurCSVLine+="\t"+b["hierog"]
     sSourcePath=os.path.join(dstimgfolder,b["hierog"])
     sDestPath=os.path.join(csvExtractImgFolder,b["hierog"])
     shutil.copy(sSourcePath,sDestPath)
 sCurItem2="<tr id='HHH"+b["gardi"]+"'>\r"
 sCurItem2+="<td>"+b["gardi"].replace("+"," ").replace("-"," ").replace(":"," ")+"</td>\r"
 sCurItem2+="<td>"
 if 'N Möller' in b:
    sCurItem2+=b['N Möller']
 sCurItem2+="</td>"
 sCurItem2+='<td><img height="50" width="50"></td>\r'   #on n'affichera l'image qu'au moment où ce sera nécessaire
 #sCurItem2+='<td><img width="50"></td>\r'   #on n'affichera l'image qu'au moment où ce sera nécessaire
 sCurItem2+='<td>'
 sTranslitUnicode=""
 sTranslitAscii=""
 if "translit" in b:
  tr=b["translit"]
  sTranslitUnicode=", ".join(a["unicode"] for a in tr)
  sTranslitAscii=", ".join(a["ascii"] for a in tr)
  sCurItem2+=sTranslitUnicode
 sCurCSVLine+="\t"+sTranslitUnicode+"\t"+sTranslitAscii
 sCurItem2+="</td>\r"
 sCurItem2+="<td>"
 if b["gardi"] in frequencies:
  sCurItem2+=str(frequencies[b["gardi"]])
 elif "ligature" in b:
  sCurItem2+="(ligat)"
 sCurItem2+="</td>\r"
 hasItem=False;
 nAku=0
 nCrosefinte=0
 nWimmer=0
 for i in range(0,6 ):
  sCurItem2+="<td>"
  for hd in b["hieratogram_data"]:
   if hd["html_column"]==i:
    #curCat=dcat[hd["textContentType"]] if (hd['extractedFrom']=='AKU' and hd["textContentType"] in dcat) else "C98-UNK"
    curCat=dcat[hd["textContentType"]] if ("textContentType" in hd and hd["textContentType"] in dcat) else "C98-UNK"
    sCurItem2+="<div class='hier "+curCat+"' id='"+hd["id"]+"' >"
    if hd['extractedFrom']=='AKU':
        sCurItem2+="<span class='tooltiptext'><a href='https://aku-pal.uni-mainz.de/signs/"+hd["id"]+"' target='_blank'>Aku "+hd["id"]+"</a><br/>"+hd["textContentType"]+"<br/>"+hd["text"]+"<br/>"+hd["date"]+"</span>"
        nAku=nAku+1
    elif hd['extractedFrom']=='Crosefinte':
        #sCurItem2+="<span class='tooltiptext'><a href='http://ecriture.egypte.free.fr/ressources/Moller-hieratique_actualise_tome2.pdf' target='_blank'>Moller "+hd["N Möller"]+"</a><br/>"+hd["text"]+"</span>"
        sCurItem2+="<span class='tooltiptext'><a href='http://ecriture.egypte.free.fr/ressources/Moller-hieratique_actualise_tome2.pdf' target='_blank'>Moller "+b["N Möller"]+"</a><br/>"+hd["text"]+"</span>"
        nCrosefinte=nCrosefinte+1
    elif hd['extractedFrom']=='Wimmer':
        sCurItem2+="<span class='tooltiptext'>Wimmer<br/>Plate "+hd["wimmerPlate"]+"<br/>"+hd["date"]+"</span>"
        nWimmer=nWimmer+1
    sCurItem2+='<img />'
    #sCurItem2+='<img width="50" />'
    sCurItem2+='</div>'
    hasItem=True;
  sCurItem2+="</td>"
 # colonne pour l'ordre
 sCurItem2+="<td>"+getOrderString(b)+"</td>"
 sCurItem2+='<td>'
 sCurCSVLine+="\t"+str(nAku)+"\t"+str(nCrosefinte)+"\t"+str(nWimmer)+"\n"
 csvlines.append({"text":sCurCSVLine,"order":getOrderString(b)})
 if "translit" in b:
  tr=b["translit"]
  # on néglige les - et les . dans la colonne qui sert à la recherche (pour pouvoir chercher Hm.t comme Hmt)
  sCurItem2+=",".join(a["ascii"] for a in tr).replace("-","").replace(".","")
 sCurItem2+="</td>" 
 sCurItem2+="</tr>\r"
 # colonne pour la recherche sur la translitération
 if hasItem:
  sTableContent+=sCurItem2

sHtml=sHtml.replace("XXXMAINTABLECONTENT",sTableContent)

textfile2=open(outhtmlpath,'wb')
textfile2.write(sHtml.encode("utf8")) 
textfile2.close()
if generateCSVextract:
    csvlines=sorted(csvlines, key=lambda x: x["order"])
    csvFile=open(csvExtractFilePath,'wb')
    csvFile.write("id\tTranslitUnicode\tTransitAscii\tnAku\tnCrosefinte\tnWimmer\n".encode("utf8"))
    for l in csvlines:
        csvFile.write(l["text"].encode("utf8"))
    csvFile.close()
