from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.request
import os.path
import time 
import json

# Serialize data into file:
#json.dump( data, open( "file_name.json", 'w' ) )
# Read data from file:
#data = json.load( open( "file_name.json" ) )


dirtxt=r'E:\personal\EtudesEgyptologie\séminaireEgypto\MollerHieratique\AKUscrapingResults\txt'
jsontxtfile=r'E:\personal\EtudesEgyptologie\séminaireEgypto\MollerHieratique\AKUscrapingResults\ramsesfrequencies.json'
txtfiles=os.listdir(dirtxt)
datatoadd=[]
frequencies={}
if os.path.exists(jsontxtfile):
 frequencies=json.load(open(jsontxtfile))
else:
 for txtfile in txtfiles:
  if txtfile[-4:]=='.txt':
   hiera_id=txtfile[:-4]
   print("Processing " + hiera_id)
   fin=open(dirtxt+'\\'+txtfile,encoding='utf-8')
   rows = ( line.split('\t') for line in fin )
   d = { row[0]:row[1][:-1] for row in rows }
   d['id']=hiera_id
   frequencies[d['Manuel de Codage (MdC)']]=-1
 json.dump(frequencies, open(jsontxtfile, "w"))

# prepare selenium
driverpath="E:\\personal\\chromePortable\\chromedriver.exe"
from selenium.webdriver.chrome.options import Options
chromepath="e:\\personal\\chromePortable\\App\\Chrome-bin\\chrome.exe"
chromeoptions=Options()
chromeoptions.binary_location=chromepath
browser = webdriver.Chrome(executable_path=driverpath,options=chromeoptions)
from selenium.webdriver.common.by import By
 
# log into Ramses
browser.get("http://ramses.ulg.ac.be/login")
time.sleep(3)
browser.find_element_by_id("username").send_keys("philippe.hennebert@student.uliege.be")
browser.find_element_by_id("password").send_keys("Ubikkk11ramses")
buttons=browser.find_elements_by_xpath("//button[@type='submit']")
buttons[0].click()
WebDriverWait(driver=browser, timeout=10).until(
    lambda x: x.execute_script("return document.readyState === 'complete'")
)

for k in sorted(frequencies.keys()):
    browser.get("http://ramses.ulg.ac.be/search/mdc?request="+k)
    WebDriverWait(driver=browser, timeout=2).until(
        lambda x: x.execute_script("return document.readyState === 'complete'")
    )
    descriptionResults=browser.find_elements_by_xpath("//section[@class='searchResult']/div[1]")
    if len(descriptionResults)==1:
      s=descriptionResults[0].text.split(" ")[0]
      if s.isdigit():
       frequencies[k]=int(s)
       print("Frequencies of " + k + " is " + s)
    descriptionResults=browser.find_elements_by_xpath("//div[@role='alert']")
    if len(descriptionResults)>=1:
      if 'aucun résultat' in descriptionResults[0].text:
        frequencies[k]=0
    
json.dump(frequencies, open(jsontxtfile, "w"))
