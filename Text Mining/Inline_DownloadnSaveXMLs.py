# -*- coding: utf-8 -*-
"""
Created on Mon Nov 19 20:13:43 2018

@author: Kapil.Gurjar
"""

from bs4 import BeautifulSoup
import requests
import ntpath
import os
import shutil
from urllib.request import urlopen
from contextlib import closing
from zipfile import ZipFile
import zipfile 
import glob
from os import listdir
from os.path import isdir,join

def DownloadZip (link:str, destPath:str):
    with closing(urlopen(link)) as r:
        with open(destPath, 'wb+') as f:
            shutil.copyfileobj(r, f)

def CreateDir(path: str):
    try:
        os.mkdir(path)
    except FileExistsError:
        shutil.rmtree(path)
        os.mkdir(path)
    

dirpath=r"F:\Pipeline\Source\InlinePipelineAutomatedLoad"+"\\"+r'\\Inline\\'#+str(datetime.now().year)+str(datetime.now().month).zfill(2)+str(datetime.now().day).zfill(2)

link=r"https://dailymed.nlm.nih.gov/dailymed/spl-resources-all-drug-labels.cfm"
links=[]
page_response = requests.get(link, timeout=5)
page_content = BeautifulSoup(page_response.content, "html.parser")
for article in page_content.find_all('li',{'data-ddfilter':'human prescription labels'}):
    for a in article.find_all('a',href=True):
        links.append(a['href'])

CreateDir(dirpath+"Dailymed")

for link in links:
    ftpPath=dirpath+r'\\'+ntpath.basename(link)
    DownloadZip(link,ftpPath)
    print("Downloaded file "+str(ntpath.basename(link)))
    with ZipFile(ftpPath, 'r') as zip:
        zip.extractall(dirpath)
    os.remove(ftpPath)
    print("Extracted file "+str(ntpath.basename(link)))
    for zipf in glob.iglob(dirpath+"\\prescription\\*.zip"):
        with ZipFile(zipf,'r') as zip:
            zip.extractall(dirpath+"\prescription")
        os.remove(zipf)
    for xmlFile in glob.iglob(dirpath+"\\prescription\\*.xml"):
        shutil.move(xmlFile,dirpath+r"\\Dailymed")
    shutil.rmtree(dirpath+"\\prescription")
    print("Filtered only xml files from "+str(ntpath.basename(link)))

link=r"https://www.accessdata.fda.gov/cder/ndctext.zip"
ftpPath=dirpath+r'\\'+ntpath.basename(link)
DownloadZip(link,ftpPath)
print("Downloaded file "+str(ntpath.basename(link)))
with ZipFile(ftpPath, 'r') as zip:
        zip.extractall(dirpath+r"\\FDA")
os.remove(ftpPath)
os.remove(dirpath+r"\\FDA\\package.txt")
print("Extracted file "+str(ntpath.basename(link)))



