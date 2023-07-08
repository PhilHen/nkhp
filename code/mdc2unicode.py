# on inclut le code de Christian Casey MdC2Unicode
dAscii2Transliteration = { '!': 'H', '#': 'Ḫ', '$': 'H̲', '%': 'S', '&': 'T', '*': 'Ṯ', '+': 'Ḏ', '@': 'Ḥ', 'A': 'ꜣ', 'C': 'Ś', 'D': 'ḏ', 'H': 'ḥ', 'O': 'Q', 'Q': 'Ḳ', 'S': 'š', 'T': 'ṯ', 'V': 'h̭', 'X': 'ẖ', '\\': '𓏞', '^': 'Š', '_': 'D', 'a': 'ꜥ', 'c': 'ś', 'i': 'ỉ', 'o': 'q', 'q': 'ḳ', 'v': 'ṱ', 'x': 'ḫ' }
def unicodeTransliteration(sAscii):
    sUnicode = ''
    for i, c in enumerate(sAscii):
        if c in dAscii2Transliteration.keys():
            sUnicode += dAscii2Transliteration[c]
        else:
            sUnicode += c
    return sUnicode
# fin du code MdC2Unicode

dUnicode2Ascii={}
for k,v in dAscii2Transliteration.items():
    dUnicode2Ascii[v]=k

def unicode2mdc(sUnicode):
    #normalize yod
    sMdc=""
    sUnicode=sUnicode.replace(u"\u0069\u0486",u"\u1EC9")
    sUnicode=sUnicode.replace(u"\u0069\u0313",u"\u1EC9")
    for i,c in enumerate(sUnicode):
        if c in dUnicode2Ascii.keys():
            sMdc+=dUnicode2Ascii[c]
        else:
            sMdc+=c
    return sMdc

    


    
