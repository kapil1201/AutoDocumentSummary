
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 28 12:44:43 2019

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
RequiredFiles=["countries.txt","conditions.txt","design_groups.txt"," design_outcomes.txt","designs.txt",\
               "detailed_descriptions.txt","eligibilities.txt","interventions.txt","intervention_other_names.txt","sponsors.txt","studies.txt"]
			   
pipeline=r"F:\Pipeline\Source\InlinePipelineAutomatedLoad"+r'\\Pipeline\\'
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
print("Downloaded file "+str(ntpath.basename(link)))
archive = zipfile.ZipFile(ftpPath)

CreateDir(pipeline+r"\\PipeDelimitedExport")

for file in archive.namelist():
    if file in RequiredFiles:
        archive.extract(file, pipeline+r"\\PipeDelimitedExport")
archive.close()
os.remove(ftpPath)
print("Extracted required files from "+str(ntpath.basename(link)))
link=r"https://clinicaltrials.gov/AllPublicXML.zip"
ftpPath=pipeline+r'\\'+ntpath.basename(link)
DownloadZip(link,ftpPath)
CreateDir(pipeline+r"\\AllPublicXML")
print("Downloaded file "+str(ntpath.basename(link)))

with ZipFile(ftpPath, 'r') as zip:
        zip.extractall(pipeline+r"\\AllPublicXML")
os.remove(ftpPath)
directs=[f for f in listdir(pipeline+r"AllPublicXML") if isdir(join(pipeline+r"AllPublicXML/"+f))]
for d in directs:
    path=pipeline+r"AllPublicXML\\"+d+'\\'+'*.xml'
    for filepath in glob.iglob(path):
        shutil.move(filepath, pipeline+r"AllPublicXML\\"+ntpath.basename(filepath))
    shutil.rmtree(pipeline+r"AllPublicXML\\"+d)
print("Extracted and cleaned file "+str(ntpath.basename(link)))
