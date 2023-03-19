from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import HTMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import BytesIO
from bs4 import BeautifulSoup
import re
import io
import fitz


def extractbox(sStyle):
    result={}
    for s in ['left', 'top', 'width', 'height']:
        m = re.findall(s+":(\d+)px",sStyle)
        if len(m)>=1:
            result[s]=int(m[0])
    return result

def deduceSeparators(soup,nVerticalOffset):
    verticals=[]
    horizontals=[]
    horizontalset=set()
    spans=soup.find_all("span")
    for span in spans:
        sStyle=span.get("style")
        if "border: black 1px solid" in sStyle:
            box = extractbox(sStyle)
            if 'top' in box:
                box['top']+=nVerticalOffset
            if 'width' in box and 'height' in box:
                if box['width']<=2 and 'left' in box:
                    verticals.append(box)
                if box['height']<=2 and 'top' in box:
                    horizontals.append(box)
    return verticals, horizontals

def deduceRowAndColForItem(w,rows,columns):
    #w must be a word from get_text("words"), or bbox from Page.get_image_bbox
    midHorizontalWord = (w[0]+w[2])/2
    midVerticalWord = (w[1]+w[3])/2
    rowDeduced=-1
    colDeduced=-1
    for i in range(0, len(rows)):
        if midVerticalWord>=rows[i]['top'] and midVerticalWord<=rows[i]['bottom']:
            rowDeduced=i
    for i in range(0, len(columns)):
        if midHorizontalWord>=columns[i]['left'] and midHorizontalWord<=columns[i]['right']:
            colDeduced=i
    return rowDeduced, colDeduced

path=r'E:\personal\EtudesEgyptologie\séminaireEgypto\Moller-hieratique_actualise_tome2.pdf'
outputpath=r'E:\personal\EtudesEgyptologie\séminaireEgypto\MollerHieratique\mdcToMoller.txt'

htmlPages={}
for i in range(11, 82):
    print("Now extracting html for " + str(i))
    rsrcmgr = PDFResourceManager()
    retstr = BytesIO()
    device = HTMLConverter(rsrcmgr, retstr, codec='utf-8', laparams=LAParams())
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    pagenos=set()
    for pageNumber,page in enumerate(PDFPage.get_pages(fp, pagenos, maxpages=0, password="",caching=True, check_extractable=True)):
        if pageNumber==i:
            interpreter.process_page(page)
            data = retstr.getvalue()
            file=open('E:\\personal\\EtudesEgyptologie\\séminaireEgypto\\MollerHieratique\\pdfextract\\'+str(pageNumber)+".html","wb")
            htmlPages[i]=data.decode("utf-8")
            #file.write(data.encode('utf-8'))
            file.write(data)
            file.close()
            data = ''
            retstr.truncate(0)
            retstr.seek(0)
    fp.close()
    device.close()
    retstr.close()


matches={}
for nPage in range(12, 80):
    print("Now extracting soup for " + str(nPage))
    sPage=htmlPages[nPage]
    soup=BeautifulSoup(sPage, 'html.parser')
    #on cherche la position verticale du texte "actualisation"
    verLiteralFromHtml = extractbox(soup.find(text=re.compile('Actualisation')).find_parent("div").get("style"))['top']
    pdf_file=fitz.open(path)
    page=pdf_file[nPage]
    wordsOnPage=page.get_text("words")
    verLiteralFromFitz=list(filter(lambda item: item[4]=='Actualisation', wordsOnPage))[0][1]
    verticalOffset=int(verLiteralFromFitz-verLiteralFromHtml)
    #on cherche les séparateurs horizontaux et verticaux dans le html (en utilisant l'offset)
    verSep, horSep = deduceSeparators(soup,verticalOffset)
    #on déduit les colonnes et les lignes pertinentes, en choisissant les séparateurs qui intersectent
    # la verticale passant par le mot "Moller", et l'horizontale passant par le mot "Môller"
    wordMoller = list(filter(lambda item: item[4]=='MÖLLER', wordsOnPage))[0]
    xMoller=(wordMoller[0]+wordMoller[2])/2
    yMoller=(wordMoller[1]+wordMoller[3])/2
    verticalSeparatorSet=set()
    for v in verSep:
        if v['top']<=yMoller and v['top']+v['height']>=yMoller:
            verticalSeparatorSet.add(v['left'])
    vSeps=sorted(verticalSeparatorSet)  #ceci sont les vraies limites des colonnes
    columns=[]
    for i in range(0,len(vSeps)-1):
        columns.append({'left': vSeps[i], 'right': vSeps[i+1]})
    horizontalSeparatorSet=set()
    for h in horSep:
        if h['left']<=xMoller and h['left']+h['width']>=xMoller:
            horizontalSeparatorSet.add(h['top'])
    hSeps=sorted(horizontalSeparatorSet)
    rows=[]
    for i in range(0, len(hSeps)-1):
        if hSeps[i]>=yMoller:
            rows.append({'top': hSeps[i], 'bottom': hSeps[i+1]})
    
    for w in wordsOnPage:
        r,c = deduceRowAndColForItem(w,rows,columns)
        if r>=0 and c>=0 and c<2:
            key = 'mdc/nmoller'.split('/')[c]
            if not(key in rows[r]):
                rows[r][key]=w[4]
            else:
                rows[r][key]+=' '+w[4]

    for h in rows:
        if ('mdc' in h) and ('nmoller' in h):
            matches[h['mdc']]=h['nmoller']
            

textfile=open(outputpath,'wb')
for k,v in matches.items():
    textfile.write((k+"\t"+v+"\n").encode("utf8"))
textfile.close()
