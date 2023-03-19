import os
import base64
import json
import shutil
import mysql.connector
import re, string
import json

rootdir=r"d:\hieraproject"
dstwebserverfolder=r"d:\hieratable"
generateCSVextract=True
csvExtractImgFolder=os.path.join(rootdir,"P1_hieratable","IntermediateData","extractForTranslitDir")
csvExtractFilePath=os.path.join(rootdir,"P1_hieratable","IntermediateData","extractForTranslit.csv")


#connect to database
hieradb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="pTurin1880!",
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
          " if(allTransliterations is null, '', allTransliterations) FROM signsAndGroups"
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

outfilepath2=os.path.join(dstwebserverfolder,"hiera.htm")

#load rawAKUCrosefintedata (i.e. all hieratogram metadata) from mysql database
rawAKUCrosefintedata={}
sSql = "select graphemes.name, M1.name, G1.value, sources.name  from graphemes, metadatatypes M1,graphemesmetadata G1,sources " + \
     "where G1.grapheme_id=graphemes.id and G1.metadatatype_id=M1.id and sources.id=graphemes.source_id " + \
     "and (sources.name='Crosefinte' or sources.name='Wimmer' or (sources.name='AKU' " + \
     "and exists(select 1 from graphemesmetadata G2, metadatatypes M2 where G1.grapheme_id=G2.grapheme_id and G2.metadatatype_id=M2.id " + \
     "and M2.name='date' and (G2.value like 'Dritte Zwischenzeit%' or G2.value like 'Neues%')))) " + \
    " order by graphemes.name, M1.name"
c=hieradb.cursor()
c.execute(sSql)
for x in c.fetchall():
    if not(x[0] in rawAKUCrosefintedata):
        rawAKUCrosefintedata[x[0]]={'id':x[0], 'extractedFrom':x[3]}
    sx2 = x[2]
    if x[1]=="wimmerPlate":
        sx2=sx2.split("_")[2]
    rawAKUCrosefintedata[x[0]][x[1]]=sx2
c.close()

datatoadd=[]
for k,d in rawAKUCrosefintedata.items():
    hiera_id=d['id']
    sHieratOutputFileName="h"+str(hiera_id)+".svg"    #hiératogramme h1234.svg
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
    hd['registreCateg']=dcat[hd["textContentType"]] if (hd['extractedFrom']=='AKU' and hd["textContentType"] in dcat) else "C99-OTH"
 b['hieratogram_data']=sorted(b['hieratogram_data'], key=lambda x:x['registreCateg'])
print("fin du tri")


sHtmlHeader2="""<html>
<head><meta charset="utf-8"></head>
<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.12.1/css/jquery.dataTables.css">
<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/fixedheader/3.2.4/css/fixedHeader.dataTables.min.css">
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>
<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.12.1/js/jquery.dataTables.js"></script>
<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/responsive/2.3.0/js/dataTables.responsive.min.js"></script>
<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/fixedheader/3.2.4/js/dataTables.fixedHeader.min.js"></script>
<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/plug-ins/1.12.1/sorting/natural.js"></script>

<style>
/* Language */
#lang-switch img {
  width: 32px;
  height: 32px;
  opacity: 0.5;
  transition: all .5s;
  margin: auto 3px;
  -moz-user-select: none;
  -webkit-user-select: none;
  -ms-user-select: none;
  user-select: none;
}

#lang-switch img:hover {
  cursor: pointer;
  opacity: 1;
}

.fr_lang,
.en_lang {
  display: none;
  transition: display .5s;
}

.active-lang {
  display: flex;
  transition: display .5s;
}

span.active-lang {
  display: inline;
}

.active-flag {
  transition: all .5s;
  opacity: 1 !important;
}

.thanks a:link {
  text-decoration: none;
  color: skyblue;
}

.thanks a:visited {
  text-decoration: none;
  color: skyblue;
}

.thanks a:hover {
  text-decoration: underline;
}

img {
 padding: 3px;
}
.exercisesTable {
  margin-left: 60
}

table {
	border-collapse:collapse;
}

ul{ margin-top:0; margin-bottom:0 }

.thanks li {
   margin-bottom: 3px;  
   margin-top: 3px;  
}

#openSettingsButton {
	position:fixed;
	top:0;
	right:0;
	height:30px;
	width;30px;
	cursor:pointer;
}
#openDrillButton {
	position:fixed;
	top:0;
	right:40px;
	height:30px;
	width;30px;
	cursor:pointer;
}
#openThanksButton {
	position:fixed;
	top:0;
	right:70px;
	height:30px;
	width;30px;
	cursor:pointer;
}

#settingsSidebar {
  position: fixed;
  top: 0;
  right: 0;
  width: 40%;
  height: 100%;
  opacity:0.98;
  background-color:#d3d3d3;
  z-index: 10;
  display: none;
  overflow-y: scroll;
}

#drillSidebar {
  position: fixed;
  top: 0;
  right: 0;
  width: 50%;
  height: 100%;
  opacity:1;
  background-color:#d3d3d3;
  z-index: 10;
  display: none;
  overflow-y: scroll;
}

#thanksSidebar {
  position: fixed;
  padding: 10px;
  top: 0;
  right: 0;
  width: 50%;
  height: 100%;
  opacity: 1;
  /*background-color:#d3d3d3;*/
  background-color: black;
  color: #fff;  
  z-index: 10;
  display: none;
  overflow-y: scroll;
}

.closebtn {
  position: absolute;
  top: 0;
  right: 15px;
  font-size: 32px;
  margin-left: 50px;
  text-decoration: none;
  color: #818181;
  display: block;
}

.tableInSidebar {
	margin-top: 35px;
	margin-left: auto;
	margin-right:auto;
}

.topRowParent {
  text-align: center;
}
.topRowChild {
  display: inline-block;
}


.hier {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 50px;
  margin: 1px;
}

.hier img {
    max-width: 100%;
    max-height: 100%;
    width: 100%;
    height: 100%;
    padding: 0px;
    object-fit: contain;
}

/* Tooltip text */
.hier .tooltiptext {
  visibility: hidden;
  width: 120px;
  background-color: black;
  color: #fff;
  text-align: center;
  padding: 5px 0;
  border-radius: 6px;
  position: absolute;
  left: 105%;
  z-index: 1;
}

/* Show the tooltip text when you mouse over the tooltip container */
.hier:hover .tooltiptext {
  visibility: visible;
}

/* Registres de textes */
.C01-LITT {background:#D98880 }
.C02-DOC {background:#C39BD3  }
.C03-RELIG {background:#7FB3D5 }
.C04-MM {background: #76D7C4 }
.C05-ROY {background:#F7DC6F }
.C06-JUR {background:#D6DBDF   }
.C07-BES {background: #AED6F1}
.C98-UNK {background:#F4F6F6  }
.C99-OTH {background:#F4F6F6  }
.checkboxforC01-LITT {background:#D98880 }
.checkboxforC02-DOC {background:#C39BD3  }
.checkboxforC03-RELIG {background:#7FB3D5 }
.checkboxforC04-MM {background: #76D7C4 }
.checkboxforC05-ROY {background:#F7DC6F }
.checkboxforC06-JUR {background:#D6DBDF   }
.checkboxforC07-BES {background: #AED6F1}
.checkboxforC98-UNK {background:#F4F6F6  }
.checkboxforC99-OTH {background:#F4F6F6  }

</style>
<script type="text/javascript">

function translitUnicodeToMdc(s) {
    dTransliteration2Ascii = {'H':'!' , 'Ḫ':'#', 'H̲':'$','S':'%','T':'&','Ṯ':'*','Ḏ':'+','Ḥ':'@','ꜣ':'A','Ś':'C','ḏ':'D','ḥ':'H','Q':'O','Ḳ':'Q','š':'S','ṯ':'T','h̭':'V','ẖ':'X','𓏞':'\\\\','Š':'^','D':'_','ꜥ':'a','ś':'c','ỉ':'i','q':'o','ḳ':'q','ṱ':'v','ḫ': 'x'}
    var sOut="";
    for (var i = 0; i < s.length; i++) {
        var c=s[i];
        if (c in dTransliteration2Ascii) {
            sOut=sOut+dTransliteration2Ascii[c];
        } else {
            sOut = sOut + c;
        }
    }
    return sOut;
}

function hideOrShowSidebar(sSideBar,blShow) {
	document.getElementById(sSideBar+"Sidebar").style.display=blShow?"block":"none";
}


function generateDrill(nExercises) {
 var divplayarea = document.getElementById("playarea")
 //on va créer un élément avec l'id drill qu'on supprime à chaque début d'exécution
 var olddrill=document.getElementById("drill")
 if (olddrill!=null) {
	olddrill.remove()
 }
 
 blOnlyFrequent = document.getElementById("check_onlyfrequent").checked;
 blIncludeLigatures = document.getElementById("check_includeLigatures").checked;
 minFrequent = Number(document.getElementById("minFrequent").value);
 
 
 var hieros={};
 var arrHiera=[];
 var arrHieraChosen=[];
 /* on construit un hashtable de tous les hiéroglyphes avec leur fréquence au départ des données dataTable */
 for (var i=0;i<datatable.rows().data().length;i++) {
    hrow=datatable.rows().data()[i];
	rowid=datatable.row(i).node().getAttribute("id").substring(3);
	//console.log("Comparing " + rowid + " with " + hrow[0]);
    hieros[rowid]={'freq': hrow[4], 'translit': hrow[3]}
 }
 
 // on utilise la hashtable ht de tous les hiératogrammes 
 for (h in ht) {
    //console.log(ht[h])
    sFrequency="0"
    if (typeof hieros[ht[h]] !== "undefined") {
        if ("freq" in hieros[ht[h]]) {
            sFrequency = hieros[ht[h]]["freq"];
        }
    } else {
        console.log("Prob with " + ht[h])
    }
    blInclude=true;
    if (sFrequency=="(ligat)") {
        blInclude = blIncludeLigatures
    } else {
        if (blOnlyFrequent) {
            blInclude = (Number(sFrequency) >= minFrequent)
        }
    }
	if (blInclude) {
		arrHiera.push(h);
	}
 }
 if (nExercises>arrHiera.length-1) {nExercises=arrHiera.length-1;}
 //créer un tableau avec nExercises hiératogrammes choisis au hasard
 for (var i=0; i<nExercises; i++) {
  indexChosen = Math.floor(Math.random() * arrHiera.length);
  arrHieraChosen.push(arrHiera[indexChosen]);
  arrHiera.splice(indexChosen,1);
 }
 divplay = document.createElement("div")
 divplay.setAttribute("id","drill")
 tb = document.createElement("table");
 tb.setAttribute("class","exercisesTable");
 tb.setAttribute("border","1");
 tb.setAttribute("id","drillTable");
 arrCols="col_hierato/col_mdc/col_hiero/col_translit".split("/")
 for (i=0;i<arrCols.length;i++) {
  tcol = document.createElement("col");
  tcol.setAttribute("class",arrCols[i]);
  tb.appendChild(tcol);
 }
  
 for (var i=0; i<arrHieraChosen.length; i++) {
	trow = document.createElement("tr");
	td=document.createElement("td");
    tdiv=document.createElement("div")
	tdiv.setAttribute("class","hier");
    //on va chercher l'image de l'hiératogramme
    hie=ht[arrHieraChosen[i]];
    imgSrc = "img/h"+arrHieraChosen[i]+".svg";
    timg1=document.createElement("img")
    timg1.setAttribute("src",imgSrc);
    tdiv.appendChild(timg1);
	td.appendChild(tdiv);
    trow.appendChild(td);
    
    //on va chercher le code Gardiner
	td=document.createElement("td");
	ttext=document.createTextNode(hie);
	td.appendChild(ttext);
	trow.appendChild(td)

    //on va chercher l'image du hiéroglyphe
	td=document.createElement("td");
    imgSrc = "img/"+hg[hie];
	timg2 = document.createElement("img");
	timg2.setAttribute("src",imgSrc);
	timg2.setAttribute("height","50");
	timg2.setAttribute("width","50");
	td.appendChild(timg2);
	trow.appendChild(td)

    td=document.createElement("td");
	//console.log(hie);
    td.innerHTML=hieros[hie]["translit"];
    trow.appendChild(td);
    
	tb.appendChild(trow);
 }
 
 //cacher les colonnes
 tb.getElementsByClassName("col_mdc")[0].style.visibility="collapse";
 tb.getElementsByClassName("col_hiero")[0].style.visibility="collapse";
 tb.getElementsByClassName("col_translit")[0].style.visibility="collapse";
 
 divplay.appendChild(tb);
 divplayarea.appendChild(divplay);
 
 document.getElementById("showAnswersButton").removeAttribute("hidden");
}
function showAnswers() {
 var tb=document.getElementById("drillTable");
 tb.getElementsByClassName("col_mdc")[0].style.visibility="";
 tb.getElementsByClassName("col_hiero")[0].style.visibility="";
 tb.getElementsByClassName("col_translit")[0].style.visibility="";
 document.getElementById("showAnswersButton").setAttribute("hidden","hidden");
}

function setDisplayedURL(s) {
	document.getElementById("cururl").href=s;
	document.getElementById("cururl").innerHTML=s;
}

function computeURL() {
	var sURL = document.URL.split('?')[0]	//basepath
	//add language
	var isFrench=$(".fr_lang").first().hasClass("active-lang");
	sURL+= isFrench?"?lang=fr":"?lang=en";
	
    var searchGardi=$("#searchGardi").val();
    var searchMöller=$("#searchMöller").val();
    var searchMdc=$("#searchMdc").val();
	var f="";
	
	var min = parseInt($("#minFrequent").val(),10);
	var blOnlyFrequent = $("#check_onlyfrequent")[0].checked;
    var blIncludeLigatures = $("#check_includeLigatures")[0].checked;
	var t="";
    //if ($("#check_matchexact")[0].checked) {m="exact";}	else	//default value is exact
	if ($("#check_matchcontains")[0].checked) {t="contains";}	else if ($("#check_matchregex")[0].checked) {t="regex";}
	
	
    if (typeof(searchGardi)=="undefined") {searchGardi="";};
    if (typeof(searchMöller)=="undefined") {searchMöller=""};
    if (typeof(searchMdc)=="undefined") {searchMdc=""};
	searchMdc=translitUnicodeToMdc(searchMdc);
	if (searchGardi!="") {f="gardi"} else if (searchMöller!="") {f="moeller"} else if (searchMdc!="") {f="translit"};
	if (searchGardi+searchMöller+searchMdc!="") {
		sURL+="&s="+encodeURIComponent(searchGardi+searchMöller+searchMdc)+"&f="+f;
		if (t!="") {sURL+="&t="+t;}
	}
	if (blOnlyFrequent) { sURL+="&freq="+min;}
	if (!blIncludeLigatures) {sURL+="&lig=0";}
	
	return sURL;
}

function switchLanguage(activeLang) {
	//console.log("Switching to "  + activeLang);
	otherLang=(activeLang=="fr")?"en":"fr";
    $("."+activeLang+"_lang").addClass("active-lang"); 
    $("."+otherLang+"_lang").removeClass("active-lang");
    $("#lang-switch ."+activeLang).addClass("active-flag");
    $("#lang-switch ."+otherLang).removeClass("active-flag");
	setDisplayedURL(computeURL());
}

document.onreadystatechange = function() {
    document.getElementById("playarea").style.visibility=(document.readyState == "complete")?"visible":"hidden";
    document.getElementById("waitarea").style.visibility=(document.readyState == "complete")?"hidden":"visible";
	document.getElementById("urlarea").style.visibility=(document.readyState == "complete")?"visible":"hidden";
	
    if (document.readyState =="complete") {
			
	
			document.getElementById("topRow").style.textAlign="left";
			setDisplayedURL(document.URL);
            var params = new  URLSearchParams(window.location.search);   
            var searchItem = params.get("s"); 		
            var searchField = params.get("f");		//gardi, translit or moeller
            var searchType = params.get("t");		//exact, contains or regex
            var includeLigs = params.get("lig")	;	//0 or 1
            var minFrequent = params.get("freq");
			var lang = params.get("lang");
            if (minFrequent == null) {minFrequent=""};
			if (lang == null) {lang="fr"};

			switchLanguage(lang);

            if (searchItem != "") {
                    var htmlFieldSearch = "Gardi";
                    if (searchField=="translit") {htmlFieldSearch="Mdc"}
                    else if (searchField=="moeller") {htmlFieldSearch="Möller"};
                    $("#search"+htmlFieldSearch).val(searchItem);

                    if (includeLigs=="0") { $("#check_includeLigatures")[0].checked=false }
                    if (minFrequent !="") {
                            $("#check_onlyfrequent")[0].checked=true;
                            $("#minFrequent").val(minFrequent);
                    }
                    
                    if ((searchType!="exact") && (searchType!="contains") && (searchType!="regex")) {searchType="exact"};
                    arr=["exact","contains","regex"];
                    $("#check_match"+searchType)[0].checked=true;		
                    for (i=0;i<arr.length;i++) {
                            if (arr[i]!=searchType) { 
                                    $("#check_match"+arr[i])[0].checked=false; 
                            }
                    }
            }
            if (Array.from(params).length >0 ) {
                    updateDisplay();
            }
    }
};


function changeNoColor() {
    toggleHieratogramsTransparency($("#check_nocolor")[0].checked);
}

function changeCategClassVisibilities() {
    arrCategs=sCategClasses.split("/");
    for (kk=0 ; kk<arrCategs.length ; kk++) {
        blIsCurClassChecked = $("#check_cat"+arrCategs[kk])[0].checked;

        toggleClassVisibility(arrCategs[kk],blIsCurClassChecked);
    }
    updateDisplay();
}

function getUsualColorForTextCategory(sClassName) {
 console.log("Trying to find color for " + sClassName);
 for (var ii=2;ii<document.styleSheets.length;ii++) {
  for (var jj=0;jj<document.styleSheets[ii].cssRules.length;jj++) {
   if (document.styleSheets[ii].cssRules[jj].cssText.startsWith(".checkboxfor"+sClassName)) {
     return document.styleSheets[ii].cssRules[jj].style.getPropertyValue("background-color");
   }
  }
 }
}

function toggleHieratogramsTransparency(blTransparent) {
 var arrCategs=sCategClasses.split("/");
 for (var kkk=0;kkk<arrCategs.length;kkk++) {
    sClassName=arrCategs[kkk];
    for (var i=2;i<document.styleSheets.length;i++) {
      for (var j=0;j<document.styleSheets[i].cssRules.length;j++) {
       if (document.styleSheets[i].cssRules[j].cssText.startsWith("."+sClassName)) {
         if (blTransparent) {
            document.styleSheets[i].cssRules[j].style.setProperty("background-color","transparent");
         } else {
            sColor=getUsualColorForTextCategory(sClassName);
            console.log("Usual color for " + sClassName + " is " + sColor);
            document.styleSheets[i].cssRules[j].style.setProperty("background-color",sColor);
         }
       }
      }
    }
 }
}


function toggleClassVisibility(sClassName,blVisible) {
 for (i=2;i<document.styleSheets.length;i++) {
  for (j=0;j<document.styleSheets[i].cssRules.length;j++) {
   if (document.styleSheets[i].cssRules[j].cssText.startsWith("."+sClassName)) {
      s="";
      if (blVisible) {s=500; d="inline-block";} else {s=0; d="none";}
      document.styleSheets[i].cssRules[j].style.setProperty("display",d);
      document.styleSheets[i].cssRules[j].style.setProperty("max-height",s);
      document.styleSheets[i].cssRules[j].style.setProperty("max-width",s);      
    }
  }
 }
}

     
 

function displayImageForDatatableRow( row, aData, iDisplayIndex ) {
	if ($('td:eq(2) > img', row)[0].getAttribute("src") == null) {
		/* image not initialized yet */
		sGardi=row.getAttribute("id").substring(3);
        imgSrc = "img/"+hg[sGardi];
        row.getElementsByTagName('td')[2].getElementsByTagName('img')[0].setAttribute("src",imgSrc);
        hi=row.getElementsByClassName("hier");
        for (i=0;i<hi.length;i++) {
          hie=hi[i];
          id=hie.getAttribute("id");
          imgSrc="img/h"+id+".svg";
          hie.getElementsByTagName("img")[0].setAttribute("src",imgSrc);
        }
	}
    return row;
};


</script>
<body>

<div class="topRowParent" id="topRow">
	<div class="topRowChild" id="urlarea" style="visibility:hidden;"><span class="fr_lang"><b>URL du filtre en cours:</b></span><span class="en_lang"><b>URL of current filter:</b></span> <a id="cururl" href='placeholder'>placeholder</a></div>
	<div class="topRowChild" id="waitarea"><b style="background-color:yellow">Page loading - please wait / Page en cours de chargement - veuillez patienter</b></div>
</div>
<div id="drillSidebar"><a href="javascript:void(0)" class="closebtn" onclick="hideOrShowSidebar('drill',false)">&times;</a>
	<div id="playarea" style="visibility:hidden;">
		<center>
			<button onclick="generateDrill(30)"><div class="fr_lang">Génère exercices</div><div class="en_lang">Generate random test</div></button>
			<button id="showAnswersButton" hidden onclick="showAnswers()"><div class="fr_lang">Montre solutions</div><div class="en_lang">Show answers</div></button>
		</center>
	</div>
</div>
<div id="thanksSidebar"><a href="javascript:void(0)" class="closebtn" onclick="hideOrShowSidebar('thanks',false)">&times;</a>
<br/>
<b>HieraLearn (TROUVER NOM ADEQUAT)</b>
<div class="fr_lang"><ul class="thanks">
	<li>HieraLearn (TROUVER NOM ADEQUAT) est un outil d'apprentissage du hiératique du Nouvel Empire et du début de la TPI, développé par <a href="mailto:philippe.hennebert@student.uliege.be">Philippe <font style="font-variant: small-caps">Hennebert</font></a>, étudiant à l'Université de Liège, sous la supervision de <a class="thanks" href="https://www.uliege.be/cms/c_9054334/fr/repertoire?uid=u192490">Stéphane <font style="font-variant: small-caps">Polis</font></a>.</li>
	<li>Cet outil permet d'explorer de façon dynamique les paléographies de Georg <font style="font-variant: small-caps">Möller</font> (vol. II) et de Stefan <font style="font-variant: small-caps">Wimmer</font>, notamment via des filtres et recherches complexes, permettant notamment des comparaisons</li>
	<li>Un module d'entraînement à la reconnaissance de graphèmes est également accessible à l'étudiant (génération aléatoire de listes de graphèmes à identifier).</li>
</ul></div>
<div class="en_lang"><ul class="thanks">
	<li>HieraLearn (FIND PROPER NAME) is a learning tool for New Kingdom (and early TIP) hieratic, déveloped by <a href="mailto:philippe.hennebert@student.uliege.be">Philippe <font style="font-variant: small-caps">Hennebert</font></a>, student at Liège University, under the supervision of <a class="thanks" href="https://www.uliege.be/cms/c_9054334/fr/repertoire?uid=u192490">Stéphane <font style="font-variant: small-caps">Polis</font></a>.</li>
	<li>This tool aims at exploring dynamically Georg <font style="font-variant: small-caps">Möller</font>'s and Stefan <font style="font-variant: small-caps">Wimmer</font>'s paleographies, through filters and complex searches allowing for sign comparisons.</li>
	<li>A training module for grapheme recognition is also available to interested students, randomly generating graphemes lists.</li>
</ul></div>

<br/>
<b><div class="fr_lang">Remerciements</div><div class="en_lang">Thanks</div></b>
<div class="fr_lang"><ul class="thanks">
	<li>Merci à l'équipe du projet  <a href="https://aku-pal.uni-mainz.de/">AKU</a> de mettre à disposition sur leur plateforme en ligne de nombreux graphèmes sous licence CC-BY 4.0, ainsi que des métadonnées extensives, mais aussi de nous avoir envoyé des scans de haute qualité de la paléographie de Stefan <font style="font-variant: small-caps">Wimmer</font>.</li>
	<li>Merci à Stefan Jakob <font style="font-variant: small-caps">Wimmer</font> de nous avoir autorisés à utiliser les formes hiératiques des planches de sa paléographie.</li>
</ul></div>
<div class="en_lang"><ul class="thanks">
	<li>Thanks to the <a href="https://aku-pal.uni-mainz.de/">AKU</a> project team for providing an online platform with many graphemes under CC-BY 4.0 license, as well as extensive metadata, but also for sending us high-quality scans of Stefan<font style="font-variant: small-caps">Wimmer</font>'s paleography.</li>
	<li>Thanks to Stefan Jakob <font style="font-variant: small-caps">Wimmer</font> for letting us use the hieratic shapes scanned from his paleographic plates.</li>
</ul></div>

<br/>
<b><div class="fr_lang">Bibliographie</div><div class="en_lang">Bibliography</div></b>
<ul class="thanks">
	<li>Ursula <font style="font-variant: small-caps">Verhoeven</font> et al, <a href="https://aku-pal.uni-mainz.de/">Altägyptische Kursivschriften Projekt (AKU-PAL)</a></li>
	<li>Georg <font style="font-variant: small-caps">Möller</font>, <i>Hieratische Paläographie. Die Aegyptische Buchschrift in ihrer Entwicklung von der fünften Dynastie bis zur Römischen Kaiserzeit </i>I–III, Leipzig 1909-1912. I-IV: Leipzig 1927-1936, Neudruck Osnabrück 1965.</li>
	<li>Stefan Jakob <font style="font-variant: small-caps">Wimmer</font>, <i>Hieratische Paläographie der nicht-literarischen Ostraka der 19. und 20. Dynastie</i>, Ägypten und Altes Testament 28, Wiesbaden 1995.
	<li>Serge <font style="font-variant: small-caps">Rosmorduc</font> (2014). <em>JSesh Documentation</em>. [online] disponible sur: <a href="http://jseshdoc.qenherkhopeshef.org">http://jseshdoc.qenherkhopeshef.org</a> [accès 18 février 2023]</li>
	<li>Projet Ramses de l'Université de Liège, <a href="http://ramses.ulg.ac.be/">http://ramses.ulg.ac.be/</a> [online - accès 18 février 2023]</li>
	<li>Simone <font style="font-variant: small-caps">Gerhards</font>, Tobias <font style="font-variant: small-caps">Konrad</font>. „Von Bildern und Bienen – Methodenreflexionen zur digitalen paläografischen Analyse des Hieratischen“. In <i>Ägyptologische „Binsen“-Weisheiten IV. Hieratisch des Neuen Reiches: Akteure, Formen und Funktionen. Akten der internationalen Tagung in der Akademie der Wissenschaften und der Literatur | Mainz im Dezember 2019,</i> (eds. Svenja A. Gülden, Tobias Konrad, und Ursula Verhoeven), pp. 183–219. Abhandlungen der Geistes- und Sozialwissenschaftlichen Klasse – Einzelveröffentlichungen 17. Stuttgart: Franz Steiner Verlag, 2022</li>
	<li>Jean-Paul <font style="font-variant: small-caps">Crosefinte</font>, Sonia <font style="font-variant: small-caps">Labetouille</font>, Estelle <font style="font-variant: small-caps">Renaud</font>, François <font style="font-variant: small-caps">User</font>, <i>Actualisation de l'ouvrage de <font style="font-variant: small-caps">George Möller</font> Hieratische Paläographie - Tome II, de la XVIIIe dynastie (Thoutmosis III) à la XXIe dynastie</i> [online] disponible sur <a href="http://ecriture.egypte.free.fr/ressources/Moller-hieratique_actualise_tome2.pdf">http://ecriture.egypte.free.fr/ressources/Moller-hieratique_actualise_tome2.pdf</a> [accès 18 février 2023]</li>
	<li>Christian <font style="font-variant: small-caps">Casey</font>, Mdc2Unicode [online] disponible sur <a href="https://github.com/christiancasey/MdC2Unicode">https://github.com/christiancasey/MdC2Unicode</a> [accès 18 février 2023]</li>

</ul>
</div>
<div id="settingsSidebar"><a href="javascript:void(0)" class="closebtn" onclick="hideOrShowSidebar('settings',false)">&times;</a>
	<table class="tableInSidebar" border="1">
		<tr>
			<td></td>
			<td><div id="lang-switch"><img src="imgstatic/french.png" class="fr" onclick="switchLanguage('fr')" /> <img src="imgstatic/english.png" class="en" onclick="switchLanguage('en')" /></div></td>
    	</tr>
		<tr><td style="vertical-align:top"><input type="checkbox" id="check_matchexact" checked></td><td><b class="fr_lang">Correspondance exacte</b><b class="en_lang">Exact match</b>
			<div class="fr_lang"><ul>
				<li>Affiche tous les signes dont une des valeurs correspond exactement au terme de recherche.</li>
				<li>Utiliser des virgules pour séparer plusieurs termes de recherche et comparer des signes. Par exemple, dans la colonne Gardiner, la valeur F31,F40 affichera les graphèmes correspondants à F31 ET ceux correspondant à F40</li>
				<li>Dans la colonne Gardiner, la valeur Aa1 Z4 (ou Aa1+Z4 - tout séparateur est accepté sauf la virgule) affiche uniquement le groupe composé de Aa1 suivi de Z4</li>
				<li>Dans la colonne Möller, la valeur XXXIX filtrera la ligature XXXIX de la paléographie de Möller. La valeur 575+575 est équivalente (t t), ou X1+X1 dans la colonne Gardiner</li>
				<li>Dans la colonne translit, la valeur ms affichera tous les signes pouvant être translitérés par ms</li>
			</ul></div>
			<div class="en_lang"><ul>
				<li>Display all signs of which some value matches the search term</li>
				<li>Use commas to separate search terms and compare signs. For instance, in the Gardiner column, the serach term F31,F40 will display all graphemes that match F31 AND all graphemes that match F40</li>
				<li>In the Gardiner column, the search term Aa1 Z4 (or Aa1+Z4 - any separator is valid except the comma) will only display the group made of Aa1 followed by Z4</li>
				<li>In the Môller column, the search term XXXIX will display ligature XXXIX in Möller's paleography - which is equivalent to 575+575 (t t), or X1+X1 in the Gardiner column</li>
				<li>In the translit(eration) column, the search term ms will display all signs that can be transliterated as ms.</li>
			</ul></div>
			
		</td></tr>
		<tr><td style="vertical-align:top"><input type="checkbox" id="check_matchcontains"></td><td><b class="fr_lang">Correspondance-contient</b><b class="en_lang">"Contains"-match</b>
			<div class="fr_lang"><ul>
                            <li>Affiche tous les signes dont une des valeurs correspond au terme de recherche, ou tous les <b>groupes et ligatures</b> dont un des signes correspond au terme de recherche</li>
                            <li>Utiliser des virgules pour séparer plusieurs termes de recherche à des fins de comparaison. Par exemple, dans la colonne Gardiner, la valeur F31,F40 filtrera sur les graphèmes correspondants à F31, les graphèmes correspondants à F40, et tout groupe contenant l'un de ces deux graphèmes</li>
                            <li>Ce mode de recherche permet d'afficher aisément les groupes et ligatures contenant un ou plusieurs signe(s) donné(s).</li>
                            <li>Pour les colonnes Gardiner ou Möller, le terme de recherche doit correspondre à un code existant - dans la colonne Gardiner, G n'affichera donc PAS les signes Gxx des oiseaux</li>			
                            <li>Le comportement de cette recherche diffère un peu pour la colonne translitération: tous les signes ou groupes dont une translitération contient le terme de recherche seront affichées.</li>
			</ul></div>
			<div class="en_lang"><ul>
                            <li>Display all signs of which some value matches the search term, as well as <b>groups and ligatures</b> of which a sign matches the search term.</li>
                            <li>Use commas to separate several search terms for comparison purposes. For instance, in the Gardiner column, the search term F31,F40 will display all graphemes for sign F31, all graphemes for sign F40, as well as all groups containing either F31 or F40.</li>
                            <li>This search mode is designed to easily display groups and ligatures containing one or more given signs.</li>
                            <li>For the Gardiner and Möller columns, the search term must match an existing code - in the Gardiner column, G will NOT display all Gxx bird signs.</li>			
                            <li>The behaviour of this search mode is slightly different for the transliteration column: in this case, all signs or groups of which some transliteration CONTAINS the search term will be displayed.</li>
			</ul></div>
		</td></tr>
		<tr><td style="vertical-align:top"><input type="checkbox" id="check_matchregex"></td><td><b class="fr_lang">Correspondance-regex</b><b class="en_lang">Regex match</b>
			<div class="fr_lang"><ul>
                            <li>Affiche tous les signes dont une des valeurs correspond à l'expression régulière encodée comme terme de recherche.</li>
                            <li>La virgule ne peut pas être utilisée ici pour séparer plusieurs expressions régulières (utiliser la syntaxe regex usuelle de l'opérateur OU ( | ) ).</li>
                            <li>Par exemple, dans la colonne Gardiner, ^G affichera tout signe ou groupe commençant par un oiseau.</li>
                            <li>Dans la colonne Gardiner, ^G[0-9]*[a-zA-Z]*$ affichera tous les signes d'oiseaux  mais pas les groupes commençant par un oiseau.</li>
                            <li>Dans la colonne Gardiner,  ^G| G affichera tous les signes ou groupes contenant un oiseau</li>
                            <li>Dans la colonne Möller, ^[^0-9] affichera tous les codes Möller en chiffres romains - càd les ligatures et groupes identifiés comme tels dans sa paléographie</li>
			</ul></div>
			<div class="en_lang"><ul>
                            <li>Display all signs of which some values matches the regex specified as search term  (use the javascript-flavour of the regex syntax).</li>
                            <li>Commas can NOT be used here to separate several regexes ;  the usual pipe-based regex OR syntax ( | ) should be used instead.</li>
                            <li>For instance, in the Gardiner column, ^G will display all bird signs as well as groups starting with a bird.</li>
                            <li>In the Gardiner column, ^G[0-9]*[a-zA-Z]*$ will display all bird signs but not groups starting with a bird.</li>
                            <li>In the Gardiner column,  ^G| G will display all bird signs as well as groups CONTAINING a bird.</li>
                            <li>In the Möller column, ^[^0-9] will display all Roman numerals Möller codes - i.e. ligatures and groups classified as such in Möller's paleography.</li>
			</ul></div>
		</td></tr>
		<tr><td><input type="checkbox" id="check_onlyfrequent"></td>
                    <td>
                        <span class="fr_lang">Seulement les signes fréquents</span><span class="en_lang">Only frequent signs</span>
                        <br/>
                        n Ramses &gt;=<input style="width: 4em" type="number" id="minFrequent" value="5"></td></tr>
		<tr><td><input type="checkbox" id="check_includeLigatures" checked></td>
                    <td>
                        <span class="fr_lang">Inclure les ligatures et groupements</span><span class="en_lang">Include ligatures and groups</span>
                    </td>
                </tr>
	</table>
</div>
<img id="openSettingsButton" src="imgstatic/settings.png" onclick="hideOrShowSidebar('settings',true)"/>
<img id="openDrillButton" src="imgstatic/work.svg" onclick="hideOrShowSidebar('drill',true)"/>
<img id="openThanksButton" src="imgstatic/pray.svg" onclick="hideOrShowSidebar('thanks',true)"/>
<table border="1"><tbody><tr>
"""
categDescrip= { \
"C01-LITT" : ["littéraire", "literary"],\
"C02-DOC" : ["documentaire", "documentary"],\
"C03-RELIG" : ["religieux","religious"], \
"C04-MM" : ["médico-magique","medical/magical"], \
"C05-ROY" : ["royal","royal"],\
"C06-JUR" : ["juridique","judicial"],\
"C07-BES" : ["besuchertexte","besuchertexte"],\
"C99-OTH" : ["autres","other"] \
}

for c in sorted(set(dcat.values())):
  sHtmlHeader2+="<td class='checkboxfor"+c+"'><input type='checkbox' onchange='changeCategClassVisibilities()' id='check_cat"+c+"' checked><span class='fr_lang'>"+categDescrip[c][0]+"</span><span class='en_lang'>"+categDescrip[c][1]+"</span></td>"
sHtmlHeader2+="<td class='checkforfornocolor'><input type='checkbox' onchange='changeNoColor()' id='check_nocolor'><span class='fr_lang'>Censurer les couleurs</span><span class='en_lang'>Censor colors</span></td>"
sHtmlHeader2+="</tr></tbody></table>"
sHtmlHeader2+="<script>sCategClasses='"+"/".join(sorted(set(dcat.values())))+"'</script>"
sHtmlHeader2+="""
<script>
hg={"""

textfile2=open(outfilepath2,'wb')
textfile2.write(sHtmlHeader2.encode("utf8"))

    
isFirst=True
for gardikey in signsDict:
 sHtml=("" if isFirst else ",\n")
 isFirst=False
 b=signsDict[gardikey]
 sHtml+="'"+gardikey.replace("\\","\\\\") + "': '"+ b['hierog'] + "'"
 textfile2.write(sHtml.encode("utf8"))
sHtml="};\nht={"
textfile2.write(sHtml.encode("utf8"))
isFirst=True
for gardikey in signsDict:
  b=signsDict[gardikey]
  for hd in b["hieratogram_data"]:
    sHtml=("" if isFirst else ",\n")
    isFirst=False
    sHtml+="'"+hd['id']+"':'"+gardikey.replace("\\","\\\\")+"'"
    textfile2.write(sHtml.encode("utf8"))

sHtml="}</script>"
sHtml+='<table id="maintable" border="1"><thead><tr>'
sHtml+='<th>Gardiner</th>'
sHtml+='<th>Möller</th>'
sHtml+='<th>Hieroglyphe</th>'
sHtml+='<th>Translit</th>'
sHtml+='<th><center>n (Rams)</center></th>'
for ch in column_headers:
 sHtml+="<th><center>"+column_headers[ch]+"</center></th>"
sHtml+="<th>order</th>"
sHtml+="<th>translit mdc</th>"
sHtml+='</tr></thead><tbody>'
textfile2.write(sHtml.encode("utf8"))


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
  s=b["translit"]
  sCurItem2+="<br/>".join(["<b>"+k[0].upper()+"</b>:"+", ".join([a["unicode"] for a in v]) for k,v in s.items()])
  sTranslitUnicode=", ".join([", ".join([a["unicode"] for a in v]) for k,v in s.items()])
  sTranslitAscii=", ".join([", ".join([a["ascii"] for a in v]) for k,v in s.items()])
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
    curCat=dcat[hd["textContentType"]] if (hd['extractedFrom']=='AKU' and hd["textContentType"] in dcat) else "C98-UNK"
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
  s=b["translit"]
  sCurItem2+=",".join([",".join([a["ascii"] for a in v]) for k,v in s.items()])
 sCurItem2+="</td>" 
 sCurItem2+="</tr>\r"
 # colonne pour la recherche sur la translitération
 if hasItem:
  textfile2.write(sCurItem2.encode("utf8"))


sHtml="""
</tbody></table></body>
<script>
function isMatch(searchString,dataToCompare,nSearchType,nField) {
	//dataToCompare is an array of values (for instance ["wrd","Hms"] with which searchString will be compared)
	//nSearchType=1 for exact, 2 for contains, 3 for regex
	//nField=1 for gardiner, 2 for Möller, 3 for transliteration
	searchStrings=searchString.split(",");
	if ((nSearchType==1) || (nSearchType==2)) { 
		for (i=0;i<searchStrings.length;i++) {
			if (nField==1) {searchStrings[i]=searchStrings[i].replace(/[\W_]+/g," ").trim();};
			if (nField==2) {searchStrings[i]=searchStrings[i].replace(/[\W_]+/g,"+").trim();};
			if (nField==3) {searchStrings[i]=searchStrings[i].trim();};
		}
	}
	if (nSearchType==1) {
		bFound=false;
		for (i=0;i<dataToCompare.length;i++) {
			if (searchStrings.includes(dataToCompare[i])) {i=dataToCompare.length; bFound=true;}
		}
		return bFound;
	} else if (nSearchType==2) {
		bFound=false;
		for (i=0;i<dataToCompare.length;i++) {
			for (j=0;j<searchStrings.length;j++) {
				if ((dataToCompare[i]!="") && (searchStrings[j]!="")) {
					//now check if all "parts" of searchStrings[j] are in dataToCompare[i] - for transliteration, it's just string inclusion
					if (nField==3) {
						if (dataToCompare[i].includes(searchStrings[j])) {bFound=true; }
					} else {
						allPartsFound=true;parts=[];partsindata=[];
						if (nField==1) {parts=searchStrings[j].split(" ");partsindata=dataToCompare[i].split(" ");} else if (nField==2) {parts=searchStrings[j].split("+"); partsindata=dataToCompare[i].split("+");};
						for (k=0;k<parts.length;k++) {
							if (!partsindata.includes(parts[k])) {allPartsFound=false;}
						}
						if (allPartsFound) {bFound=true;}
					}
				}
			}
		}
		return bFound;
	} else if (nSearchType==3) {
		bFound=false;
		re=new RegExp(searchString);
		for (i=0;i<dataToCompare.length;i++) {
			if (re.test(dataToCompare[i])) {i=dataToCompare.length; bFound=true;}
		}
		return bFound;
	}
}
$.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
    var min = parseInt($("#minFrequent").val(),10);
    var isLigat=(data[4]=="(ligat)");
    var nRamses = parseFloat(data[4]) || 0; 
    var blOnlyFrequent = $("#check_onlyfrequent")[0].checked;
    var blIncludeLigatures = $("#check_includeLigatures")[0].checked;
    nSearchType=0;
    if ($("#check_matchexact")[0].checked) {nSearchType=1;}	else if ($("#check_matchcontains")[0].checked) {nSearchType=2;}	else if ($("#check_matchregex")[0].checked) {nSearchType=3;}
    var searchGardi=$("#searchGardi").val();
    var searchMöller=$("#searchMöller").val();
    var searchMdc=$("#searchMdc").val();
    if (typeof(searchGardi)=="undefined") {searchGardi=""};
    if (typeof(searchMöller)=="undefined") {searchMöller=""};
    if (typeof(searchMdc)=="undefined") {searchMdc=""};
    searchMdc=translitUnicodeToMdc(searchMdc);
    
    if (blOnlyFrequent && (!isLigat) && (min>nRamses)) {return false;}
    if (isLigat && (!blIncludeLigatures)) {return false;}
	
    if (searchGardi!="") {
		return isMatch(searchGardi,[data[0]],nSearchType,1);
    } else if (searchMöller!="") {
		return isMatch(searchMöller, data[1].replace("=",",").split(","),nSearchType,2);	//Möller can be of the type 626,646=LXIII - we divide that into the array ["626","646","LXIII"]
    } else if (searchMdc!="") {
		return isMatch(searchMdc,data[12].split(","),nSearchType,3);
    } else {
        //console.log("Triggered search");
        if (isLigat) {
            return blIncludeLigatures;
        } else if (!blOnlyFrequent) {
            return true;
        } else if (min<=nRamses) {
            return true;
        } else {
            return false;
        }
    }
});


$('#maintable thead tr').clone(true).addClass('filters').appendTo('#maintable thead');

var datatable = $('#maintable').DataTable( {
    orderCellsTop: true,
    fixedHeader: true,
    "fnRowCallback": displayImageForDatatableRow,
	"autoWidth": false,
    "dom": "iptl",
    fixedColumns: true,
	"columnDefs": [
		{ "width": "35px", "targets": [0,1] },
        { "width": "35px", "targets": 4, "type": "natural" },
		{ "width": "40px", "targets": [2, 5, 6, 7, 8, 9, 10], "orderable": false },
		{ "width": "50px", "targets": 3 },
        { "orderData": [11], "targets": 0 },
        { "targets": [11], "searchable": false, "visible": false    },
        { "targets": [12], "visible": false    }
	],
    initComplete: function() {
        var api=this.api();
        api.columns().eq(0).each(function (colIdx) {
            // Set the header cell to contain the input element
            var cell = $('.filters th').eq(
                $(api.column(colIdx).header()).index()
            );
            if (colIdx==0) {
              $(cell).html('<input id="searchGardi" type="text" style="width: 80px;" placeholder="ex:F31,F40,W17" />');   
            } else if (colIdx==1) {
               $(cell).html('<input id="searchMöller" type="text" style="width: 80px;" placeholder="ex:XXIX,XXX" />'); 
            } else if (colIdx==3) {
               $(cell).html('<input id="searchMdc" type="text" style="width: 80px;" placeholder="ex:ms,Aw" />'); 
            } else {
                $(cell).html(''); 
            }
        });
    }
});

function updateDisplay() {
	datatable.draw();
	setDisplayedURL(computeURL());
}

$('#searchGardi').keyup(function () {
    $('#searchMöller').val('');
    $('#searchMdc').val('');
	updateDisplay();
});

$('#searchMöller').keyup(function () {
    $('#searchGardi').val('');
    $('#searchMdc').val('');
    updateDisplay();
});

$('#searchMdc').keyup(function () {
    $('#searchGardi').val('');
    $('#searchMöller').val('');
    updateDisplay();
});

$('#check_matchexact, #check_matchcontains, #check_matchregex').change(function (event) {
    arr=["check_matchexact","check_matchcontains","check_matchregex"];
	curTarget=event.target.getAttribute("id");
	$("#"+curTarget)[0].checked=true;
	for (i=0;i<arr.length;i++) {
		if (arr[i]!=curTarget) { 
			$("#"+arr[i])[0].checked=false; 
		}
	}
	updateDisplay();
});

$('#minFrequent, #check_onlyfrequent, #check_includeLigatures').change(function () {
    updateDisplay();
});


</script>
</html>"""
textfile2.write(sHtml.encode("utf8")) 
textfile2.close()
if generateCSVextract:
    csvlines=sorted(csvlines, key=lambda x: x["order"])
    csvFile=open(csvExtractFilePath,'wb')
    csvFile.write("id\tTranslitUnicode\tTransitAscii\tnAku\tnCrosefinte\tnWimmer\n".encode("utf8"))
    for l in csvlines:
        csvFile.write(l["text"].encode("utf8"))
csvFile.close()
