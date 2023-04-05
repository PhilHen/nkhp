import sys
dynamicParts = [
    {"start":"/*--INSERTTEXTREGISTRIESCSSHERE--*/",
     "end":"/*--ENDOFTEXTREGISTRIESCSS--*/",
     "mnemonic":"XXXTEXTREGISTRIESCSSXXX"},
    {"start":"<!--STARTTDFORTEXTCATEG-->",
     "end":"<!--ENDTDFORTEXTCATEG-->",
     "mnemonic":"XXXTDFORTEXTCATEGXXX"},
    {"start":"//--STARTSCRIPTFORTEXTCATEGCLASSES--",
     "end":"//--ENDSCRIPTFORTEXTCATEGCLASSES--",
     "mnemonic":"XXXSCRIPTFORTEXTCATEGCLASSESXXX"},
    {"start":"//--STARTDEFINITIONOFHGHTOBJECTS--",
     "end":"//--ENDDEFINITIONOFHGHTOBJECTS--",
     "mnemonic":"XXXHTHGOBJECTSXXX"},
    {"start":"<!--STARTMAINTABLECONTENT-->",
     "end":"<!--ENDMAINTABLECONTENT-->",
     "mnemonic":"XXXMAINTABLECONTENT"}
]
sSourceHtmlFile = sys.argv[1]
sDestHtmlTemplate=sys.argv[2]
f = open(sSourceHtmlFile,"r",encoding="utf-8")
sHtml = f.read()
f.close()
for d in dynamicParts:
    pStart = sHtml.index(d["start"])
    pEnd = sHtml.index(d["end"])
    sHtml=sHtml[0:pStart+len(d["start"])]+"\n"+d["mnemonic"]+"\n"+sHtml[pEnd:]

f=open(sDestHtmlTemplate,'wb')
f.write(sHtml.encode("utf8"))
f.close()

    
