import os
import base64
import json
import shutil

#Crosefinte PDF extract
dirtxtpdf=r'c:\hieraproject\P1_hieratable\IntermediateData\pdfextract\txt'
sResult=''
txtfiles=os.listdir(dirtxtpdf)
for txtfile in txtfiles:
 if txtfile[-4:]=='.txt':
  hiera_id=txtfile[:-4]
  print("Processing " + hiera_id)
  fin=open(dirtxtpdf+'\\'+txtfile,encoding='utf-8')
  rows = ( line.split('\t') for line in fin )
  d = { row[0]:row[1][:-1] for row in rows }
  d['id']=txtfile[:-4]
  sResult+='\t'.join(d.values())+'\r'

outcsvpath=r"c:\hieraproject\p1_hieratable\IntermediateData\crosefintemetadata.txt"
textfile=open(outcsvpath,'wb')
textfile.write(sResult.encode("utf8")) 
textfile.close()
