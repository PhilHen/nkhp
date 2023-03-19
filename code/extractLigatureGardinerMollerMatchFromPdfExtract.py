import os
import json

dirtxtpdf=r'E:\personal\EtudesEgyptologie\DigitalResearch\P1_hieratable\IntermediateData\pdfextract\txt'

datatoadd=[]
txtfiles=os.listdir(dirtxtpdf)
for txtfile in txtfiles:
 if txtfile[-4:]=='.txt':
  hiera_id=txtfile[:-4]
  print("Processing " + hiera_id)
  fin=open(dirtxtpdf+'\\'+txtfile,encoding='utf-8')
  rows = ( line.split('\t') for line in fin )
  d = { row[0]:row[1][:-1] for row in rows }
  d['id']=hiera_id
  datatoadd.append(d)

sList=""
lines=[]
for d in datatoadd:
    sLine=d["Manuel de Codage (MdC)"]+"\t"+d["N Möller"]+"\r"
    if not(sLine in lines):
        lines.append(sLine)
        sList+=sLine
sOutFile=r"E:\personal\EtudesEgyptologie\DigitalResearch\P1_hieratable\IntermediateData\mdctomollerligatures.txt"
textfile=open(sOutFile,'wb')
textfile.write(sList.encode("utf8"))
textfile.close()
