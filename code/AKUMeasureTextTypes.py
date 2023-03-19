import os
import json
dirtxt=r'E:\personal\EtudesEgyptologie\séminaireEgypto\MollerHieratique\AKUscrapingResults\txt'
outfilepathtypes=r'E:\personal\EtudesEgyptologie\séminaireEgypto\MollerHieratique\freqtexttypes.txt'
outfilepathdates=r'E:\personal\EtudesEgyptologie\séminaireEgypto\MollerHieratique\freqdates.txt'
txtfiles=os.listdir(dirtxt)
texttypes={}
dates={}
for txtfile in txtfiles:
    if txtfile[-4:]=='.txt':
      hiera_id=txtfile[:-4]
      print("Processing " + hiera_id)
      fin=open(dirtxt+'\\'+txtfile,encoding='utf-8')
      rows = ( line.split('\t') for line in fin )
      d = { row[0]:row[1][:-1] for row in rows }
      d['id']=hiera_id
      d['extractedFrom']='AKU'
      if d['Datierung'].startswith("Dritte Zwischenzeit, 21") or d['Datierung'].startswith("Neues"):
        if "Textinhalt" in d:
            if d["Textinhalt"] in texttypes:
                texttypes[d["Textinhalt"]]+=1
            else:
                texttypes[d["Textinhalt"]]=1
        if d["Datierung"] in dates:
            dates[d["Datierung"]]+=1
        else:
            dates[d["Datierung"]]=1

outfile=open(outfilepathtypes,'wb')
for k,v in texttypes.items():
    outfile.write((k+"\t"+str(v)+"\r").encode("utf8"))
outfile.close()
outfile=open(outfilepathdates,'wb')
for k,v in dates.items():
    outfile.write((k+"\t"+str(v)+"\r").encode("utf8"))
outfile.close()
    
        
#json.dump(texttypes, open(outfilepath, "w"))
