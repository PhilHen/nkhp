from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.request
import os.path
import time 

driverpath="E:\\personal\\chromePortable\\chromedriver.exe"
from selenium.webdriver.chrome.options import Options
chromepath="e:\\personal\\chromePortable\\App\\Chrome-bin\\chrome.exe"
chromeoptions=Options()
chromeoptions.binary_location=chromepath
browser = webdriver.Chrome(executable_path=driverpath,options=chromeoptions)
from selenium.webdriver.common.by import By
resultsfolder=r'E:\personal\EtudesEgyptologie\séminaireEgypto\MollerHieratique\AKUscrapingResults'

for i in range(1, 40000):
 aku_url="https://aku-pal.uni-mainz.de/signs/"+str(i)
 #first, check if it's already present in err or txt - if so, skip
 if not(os.path.exists(resultsfolder+'\\txt\\'+str(i)+'.txt') or os.path.exists(resultsfolder+'\\err\\'+str(i)+'.txt')):
  print('Starting check for ' + str(i))
  browser.get(aku_url)
  time.sleep(0.4)
  #time.sleep(3)
  #WebDriverWait(browser, 10).until(
  # EC.presence_of_element_located((By.XPATH, "//div[@id='app' and @data-v-app]"))
  #)
  print("Wait finished")
  sResult=""
  is404=0
  errors = browser.find_elements(By.CLASS_NAME,"error")
  if len(errors)>0:
   if errors[0].text == "Error: 404":
    is404=1
  if is404==1:
   textfile=open(resultsfolder+'\\err\\'+str(i)+'.txt','w')
   textfile.write("404")
   textfile.close()
   print(str(i)+' is a 404')
  else:
   for trow in browser.find_elements(By.TAG_NAME, 'tr'):
    sResult+=trow.find_elements_by_tag_name('th')[0].text+'\t'+trow.find_elements_by_tag_name('td')[0].text+'\r'
   if sResult!='':
    textfile=open(resultsfolder+'\\txt\\'+str(i)+'.txt','wb')
    textfile.write(sResult.encode("utf8"))
    textfile.close()
    hieroglyph_urls=browser.find_elements_by_xpath("//button[@class='hieratogram-image' and ./span='Hieroglyphe']/img")
    hieratogram_urls=browser.find_elements_by_xpath("//button[@class='hieratogram-image' and ./span='SVG']/img")
    if len(hieroglyph_urls)!=0:
     urllib.request.urlretrieve(hieroglyph_urls[0].get_attribute("src"),resultsfolder+'\\svg\\'+str(i)+'_hierog.svg') 
    if len(hieratogram_urls)!=0:
     urllib.request.urlretrieve(hieratogram_urls[0].get_attribute("src"),resultsfolder+'\\svg\\'+str(i)+'_hierat.svg')
     print('Successfully saved hierat for ' + str(i))
browser.close()