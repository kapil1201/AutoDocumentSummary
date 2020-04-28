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
    

dirpath=os.path.dirname(os.path.realpath("__file__"))+"\\"+r'\\Inline\\'#+str(datetime.now().year)+str(datetime.now().month).zfill(2)+str(datetime.now().day).zfill(2)
RequiredFiles=["countries.txt","conditions.txt","design_groups.txt"," design_outcomes.txt","designs.txt",\
               "detailed_descriptions.txt","eligibilities.txt","interventions.txt","intervention_other_names.txt","sponsors.txt","studies.txt"]
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
    with ZipFile(ftpPath, 'r') as zip: 
        zip.printdir() 
        zip.extractall(dirpath)
    os.remove(ftpPath)
    for zipf in glob.iglob(dirpath+"\\prescription\\*.zip"):
        with ZipFile(zipf,'r') as zip:
            zip.printdir() 
            zip.extractall(dirpath+"\prescription")
        os.remove(zipf)
    for xmlFile in glob.iglob(dirpath+"\\prescription\\*.xml"):
        shutil.move(xmlFile,dirpath+r"\\Dailymed")
    shutil.rmtree(dirpath+"\\prescription")

link=r"https://www.accessdata.fda.gov/cder/ndctext.zip"
ftpPath=dirpath+r'\\'+ntpath.basename(link)
DownloadZip(link,ftpPath)

with ZipFile(ftpPath, 'r') as zip: 
        zip.printdir() 
        zip.extractall(dirpath+r"\\FDA")
os.remove(ftpPath)
os.remove(dirpath+r"\\FDA\\package.txt")


pipeline=os.path.dirname(os.path.realpath("__file__"))+r'\\Pipeline\\'
CreateDir(pipeline+"PipeDelimitedExport")

page_response = requests.get(r"https://aact.ctti-clinicaltrials.org/pipe_files", timeout=5)
page_content = BeautifulSoup(page_response.content, "html.parser")
for article in page_content.find_all('td',{'class':'file-archive'}):
    for a in article.find_all('a',href=True):
        link=r"https://aact.ctti-clinicaltrials.org/"+a['href']
        break
    break

ftpPath=pipeline+r'\\'+ntpath.basename(link)
DownloadZip(link,ftpPath)

archive = zipfile.ZipFile(ftpPath)

CreateDir(pipeline+r"\\PipeDelimitedExport")

for file in archive.namelist():
    if file in RequiredFiles:
        archive.extract(file, pipeline+r"\\PipeDelimitedExport")

os.remove(ftpPath)

link=r"https://clinicaltrials.gov/AllPublicXML.zip"
ftpPath=pipeline+r'\\'+ntpath.basename(link)
DownloadZip(link,ftpPath)
CreateDir(pipeline+r"\\AllPublicXML")

with ZipFile(ftpPath, 'r') as zip: 
        zip.printdir() 
        zip.extractall(pipeline+r"\\AllPublicXML")
os.remove(ftpPath)
directs=[f for f in listdir(pipeline+r"AllPublicXML") if isdir(join(pipeline+r"AllPublicXML/"+f))]
for d in directs:
    path=pipeline+r"AllPublicXML\\"+d+'\\'+'*.xml'
    print(path)
    for filepath in glob.iglob(path):
        shutil.move(filepath, pipeline+r"AllPublicXML\\"+ntpath.basename(filepath))
    shutil.rmtree(pipeline+r"AllPublicXML\\"+d)

