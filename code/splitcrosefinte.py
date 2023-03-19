import shutil
import os

crosefintesplitfile=r"E:\personal\EtudesEgyptologie\DigitalResearch\P1_hieratable\IntermediateData\crosefintetosplit.txt"
splitdir=r"E:\personal\EtudesEgyptologie\DigitalResearch\P1_hieratable\IntermediateData\pdfextract\imgtosplittest"

flist=open(crosefintesplitfile,encoding='utf-8')
listrows=(line.split('\t') for line in flist)
dlist = {r[0]:r[1][:-1] for r in listrows}
flist.close()
print(dlist)

for k,v in dlist.items():
    os.rename(os.path.join(splitdir,k+"_hierat.png"),os.path.join(splitdir,k+"a_hierat.png"))
    os.rename(os.path.join(splitdir,k+"_hierog.png"),os.path.join(splitdir,k+"a_hierog.png"))
    for i in range(1,int(v)):
        shutil.copy(os.path.join(splitdir,k+"a_hierat.png"),os.path.join(splitdir,k+chr(97+i)+"_hierat.png"))
        shutil.copy(os.path.join(splitdir,k+"a_hierog.png"),os.path.join(splitdir,k+chr(97+i)+"_hierog.png"))
