import os
import json
dirtxt=r'E:\personal\EtudesEgyptologie\séminaireEgypto\MollerHieratique\AKUscrapingResults\txt'
outfilepathTSV=r'E:\personal\EtudesEgyptologie\séminaireEgypto\MollerHieratique\allAKUdata.tsv'
sTxt=""
txtfiles=os.listdir(dirtxt)
outfile=open(outfilepathTSV,'wb')
headers={}
data=[]
for txtfile in txtfiles:
    if txtfile[-4:]=='.txt':
      hiera_id=txtfile[:-4]
      print("Processing " + hiera_id)
      fin=open(dirtxt+'\\'+txtfile,encoding='utf-8')
      rows = ( line.split('\t') for line in fin )
      d = { row[0]:row[1][:-1] for row in rows }
      d['id']=hiera_id
      d['extractedFrom']='AKU'
      for k in d.keys():
        if not(k in headers):
            headers[k]="TEMP"
      data.append(d)

hlist = list(headers.keys())
outfile.write(("\t".join(hlist)+"\n").encode("utf8"))

for d in data:
    sRow=""
    for h in hlist:
        if h in d:
            sRow+=d[h]
        sRow+="\t"
    sRow=sRow[:-1]
    outfile.write((sRow+"\n").encode("utf8"))

outfile.close()
