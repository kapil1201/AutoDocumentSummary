# -*- coding: utf-8 -*-
"""
Created on Thu Nov  8 17:10:59 2018

@author: Kapil.Gurjar
"""
import regex as re
import xml.etree.ElementTree as ET 
import glob
import pyodbc
import ntpath
from bs4 import BeautifulSoup
import pandas as pd
import nltk
import os
DB_CONN=""#<Connetion String Here>
def find_rec(node, element):
    for item in node.findall(element):
        yield item
        for child in find_rec(item, element):
            yield child

def RemoveXMLTags(Text: list):
    for k,indL in enumerate(Text):
        for j,ind in enumerate(indL):
# =============================================================================
#                 for i in re.findall(r'<content.*/content>',ind,re.DOTALL | re.I):
#                     ind=ind.replace(i,"1."+i) #additinally added bullet point to not to ignore while cleaning
# =============================================================================
            if re.match(r"<table.*?table>",ind,re.IGNORECASE | re.DOTALL):
                continue
            ind=re.sub("<linkhtml.*?linkhtml>","(linkhtml)",ind)
            ind=re.sub("<.*?>","",ind)
# =============================================================================
#             for i in range(ind.count(r"<")):
#                 try: 
#                     nodestart=ind.index(r"<")
#                     nodeend=ind.index(r">",nodestart)
#                     if re.match(".*linkhtml.*",ind[nodestart:nodeend+1],re.IGNORECASE | re.DOTALL)!=None:
#                         nodeend=ind.index(r">",nodeend+1)
#                     ind=ind.replace(ind[nodestart:nodeend+1]," ")
#                 except: 
#                     nodestart=0
#                     nodeend=0
#             nodestart=0
#             nodeend=0
# =============================================================================
            ind = re.sub("\s+"," ",ind)
            #ind=re.sub(r"(?:\[|\().*?(?:see|See).*?(?:\]|\))","",ind)
            Text[k][j]=ind.strip()
    return Text

def RemoveXMLTagsTitles(Text: list):
    for k,ind in enumerate(Text):
        ind=re.sub("<linkhtml.*?linkhtml>","",ind)
        ind=re.sub("<.*?>","",ind)
        Text[k]=ind.strip()
    return Text

def Transpose(mat: list):
    Tmat=[]
    if len(mat)>0:
        for i in range(0,len(mat[0])):
            tmp=[]
            for j in range(0,len(mat)):
                try:
                    tmp.append(mat[j][i])
                except IndexError:
                    return []
            Tmat.append(tmp)
    return Tmat

def extractIndicSent(sent: str):
    point=''
    if re.match(r".*\bindicated\..*",sent,re.IGNORECASE | re.DOTALL)!=None and re.match(r".*\bnot\W*\bindicated\b.*",sent,re.IGNORECASE | re.DOTALL)==None:
        point= 'o '+sent.strip()
    if re.match(r".*\bindicated\b.*",sent,re.IGNORECASE | re.DOTALL)!=None and re.match(r".*\bnot\W*\bindicated\b.*",sent,re.IGNORECASE | re.DOTALL)==None:
        point= 'o '+ re.search(r"\bindicated\b.*",sent,re.IGNORECASE | re.DOTALL).group().replace("indicated","").strip()
    
    if point!='' and len(point)>3:
        return point[:2]+point[2].upper()+point[3:]
    else:
        return ''
    
output=[]
# =============================================================================
# f=open(r"E:\xmlTest.csv","a+",encoding='utf-8')
# f.write(r"FileName"+","+r"NDC"+","+r'"Indications"'+","+r"Dosage"+"\n")
# =============================================================================
#log=open("E:/xmlLogs.txt","a+",encoding='utf-8') 

#sent_detector=nltk.data.load('tokenizers/punkt/english.pickle')

conn = pyodbc.connect(DB_CONN)
cursor=conn.cursor()
IgnoreNDC=[]
IgnoreNDC=cursor.execute("select distinct Product_NDC from [dbo].[inline_master_file_exsiting]").fetchall()
# =============================================================================
# readlog=open("E:/Relabels.txt","r")
# import shutil
# for filename in readlog.read().split("\n"):
#     filepath=r'D:\Inline XML Parsing\XMLs\Dailymed_source\Accepted_Files\\'+filename
#     shutil.copy(filepath,r"D:\Inline XML Parsing\XMLs\Dailymed_source\Accepted_Files\Relabel")
# readlog.close()   
# =============================================================================

ExList=[]
#tempf=open("E:/xmltest.txt","a+")
#from os import listdir
#from os.path import isfile, join
#AcceptedFiles = [f for f in listdir(r"D:\Inline XML Parsing\XMLs\Dailymed_source\Error_Files\Accepted Files") if isfile(join(r"D:\Inline XML Parsing\XMLs\Dailymed_source\Error_Files\Accepted Files", f))]
#RelabelFiles = [f for f in listdir(r"D:\Inline XML Parsing\XMLs\Dailymed_source\Accepted_Files\Relabel") if isfile(join(r"D:\Inline XML Parsing\XMLs\Dailymed_source\Accepted_Files\Relabel", f))]
unitList=["mg",r"kg",r"ml",r"mm2",r"mL/kg",r"mg/kg",r"mcg/kg/h",r"mL",r"g",r"ppm",r"µg",r"L",r"m^2",r"million",r"tablet",r"tablets"\
          r"milligrams",r"grams",r"hours",r"hrs",r"vp",r"MG",r"UNT",r"mg/day",r"mg/m2",r"mg/m2",r"gms",r"Teaspoon",r"Tablespoon",r"Spoon",r"tsp",r"drops",r"drop"]
ratioList=[r'INR',r'%']
numword=['one','two','three','four','five','six','seven','eight','nine','ten']
dosKeywords=[r"Usual Adult Dosage",r"recommended dose",r"Usual Oral Dosage",r"Hepatic Impairment",r"Renal Impairment",\
             r"recommended starting dose",r"usual starting dose",r"average oral dose",r"average effective dose",r"average dose",\
             r"Recommended Dosage",r"recommended daily dose",r"recommended daily maintenance dosage",r"recommended initial dose",\
             r"usual daily dose",r"usual range",r"single daily dose",r"initial dose",r"initial dosage",r"Total Daily Dose Range",\
             r"Recommended Pediatric Dosage",r"Recommended Adult Dosage",r"Adults",r"Children",r"Geriatric Use",r"65 years of age or older",\
             r"greater than or equal to 75 years of age",r"Pediatric Patients",r"Children over 6 years and adolescents"]


dosFilter = re.compile(r'.*(?:\d|\b%s\b).*(?:%s)\b.*' % ('|'.join(numword) ,'|'.join(unitList)), re.IGNORECASE | re.DOTALL)
dosFilterRto = re.compile(r'.*(?:%s)\b.*(?:\d|\b%s\b).*' % ('|'.join(ratioList),'|'.join(numword) ), re.IGNORECASE | re.DOTALL)

for filepath in glob.iglob(r'F:\Pipeline\Source\InlinePipelineAutomatedLoad\Inline\Dailymed\*.xml'):
    #print(filepath)
    #print(ntpath.basename(filepath))
    tree=ET.parse(filepath)#r"D:\Inline XML Parsing\XMLs\0df74ba1-1aa6-467c-92e7-6b017c7c6bce.xml")
    file=open(filepath,"rb").read()
    file=file.decode('utf-8')
    root=tree.getroot()
    indication=""
    dosage=""
    ndcALL=set()
    ProductName=set()
    MoleculeName=set()
    MolDisplayName=set()
    indicTitles=[]
    indicText=[]
    dosTitles=[]
    dosText=list(list())
    cname=[r"a-a spectrum",r"adrian pharmaceuticals, llc",r"aidarex pharmaceuticals llc",r"all pharma, llc",r"altura pharmaceuticals, inc.",r"american health packaging",r"angiodynamics",r"apace packaging",r"aphena pharma solutions",r"apotheca",r"apothecary shop wholesale inc.",r"a-s medication solutions",r"atlantic biologicals corps",r"avera mckennan hospital",r"avkare, inc.",r"avpak",r"bedford laboratories",r"blenheim pharmacal, inc.",r"bryant ranch prepack",r"c.o. truxton, inc.",r"cardinal health",r"carilion materials management",r"central texas community health centers",r"contract pharmacy services-pa",r"denison labs",r"denton pharma",r"department of state health services, pharmacy branch",r"dept health central pharmacy",r"direct rx",r"dispensing solutions, inc.",r"general injectables & vaccines, inc",r"golden state medical supply",r"h. j. harkins company, inc.",r"halyard health",r"hhs/program support center/supply service center",r"international laboratories, inc.",r"kaiser foundation hospitals",r"keltman pharmaceuticals inc.",r"lake erie medical & surgical supply dba quality care products llc",r"lannett company, inc.",r"legacy pharmaceutical packaging",r"liberty pharmaceuticals, inc.",r"life line home care services, inc.",r"llc federal solutions",r"major pharmaceuticals",r"mckesson corporation",r"med-health pharma, llc",r"medimetriks pharmaceuticals",r"medline industries, inc.",r"medsource pharmaceuticals",r"medvantx, inc.",r"morton grove pharmaceuticals, inc.",r"nationwide pharmaceutical, llc",r"ncs healthcare of ky, inc dba vangard labs",r"northwind pharmaceuticals",r"nucare pharmaceuticals",r"pd-rx pharmaceuticals, inc.",r"pharmaceutical associates, inc.",r"pharmakon, llc",r"physicians total care, inc.",r"precision dose inc.",r"preferred pharmaceuticals, inc.",r"proficient rx",r"readymeds",r"rebel distributors",r"redpharm drug inc.",r"remedyrepack inc.",r"rxchange co.",r"safecor health, llc",r"sina health inc",r"sircle laboratories",r"st. marys medical park pharmacy",r"stat rx usa llc",r"state of florida doh central pharmacy",r"strategic pharmaceutical solutions, inc. dba vetsource",r"tya pharmaceuticals",r"udl laboratories, inc.",r"unit dose services",r"us medsource, llc",r"vistapharm"]
    
    
    def IsRepack():
        for item in root.findall('./{urn:hl7-org:v3}author/{urn:hl7-org:v3}assignedEntity/{urn:hl7-org:v3}representedOrganization/{urn:hl7-org:v3}assignedEntity'):
            for child in item.iter():
                if child.tag=="{urn:hl7-org:v3}code" and "code" in child.attrib:
                    if child.attrib['code'] in ["C84731","C73606"]:
                        return 1
    def IsCompRepack():
        for item in root.findall('./{urn:hl7-org:v3}author/{urn:hl7-org:v3}assignedEntity/{urn:hl7-org:v3}representedOrganization'):
            for child in item.findall("./"):
                if child.tag=="{urn:hl7-org:v3}name":
                    if child.text.lower() in cname:
                        return 1
    if IsCompRepack()==1 or IsRepack==1:
        continue
    
# =============================================================================
#     def inner():
#         for item in root.findall('./{urn:hl7-org:v3}author/{urn:hl7-org:v3}assignedEntity/{urn:hl7-org:v3}representedOrganization/{urn:hl7-org:v3}assignedEntity'):
#             for child in item.iter():
#                 if child.tag=="{urn:hl7-org:v3}code" and "code" in child.attrib:
#                     if child.attrib['code'] =="C73607":
#                         open("E:/Relabels.txt","a+").write(ntpath.basename(filepath)+"\n")
#                         return 1
#     if inner()==1:
#         continue
# =============================================================================
    
    for item in root.findall('./{urn:hl7-org:v3}component/{urn:hl7-org:v3}structuredBody/{urn:hl7-org:v3}component/{urn:hl7-org:v3}section'):
        section=ET.tostring(item).decode("utf-8")
        section=section.replace("ns0:","")
        #open("E:/xmltest.txt","a+").write(section)
# =============================================================================
#         highlight = re.search("<highlight.*highlight>",section,re.IGNORECASE | re.DOTALL)
#         if highlight!=None: 
#             highlight=highlight.group()
#             section=section.replace(highlight,"")
# =============================================================================
        isIndication=0
        isDosage=0  
        nodestart=0
        nodeend=0
        indTl=None
        dosTl=None
        for child in ET.fromstring(section).iter():
            if child.tag=="code":
                    if "code" in child.attrib:
                        if child.attrib['code'] =="34068-7":
                            isDosage=1
                        elif child.attrib['code'] =="34067-9":
                            isIndication=1
            
            if isIndication==0 and child.tag=="title":
                if re.match(r".*\b(?:INDICATION|INDICATIONS)\b.*",str(ET.tostring(child).decode("utf-8")),re.IGNORECASE | re.DOTALL)\
                and len(indicText)==0:
                    isIndication=1
                    
            if isDosage==0 and child.tag=="title":
                if re.match(r".*\bDOSAGE\b.*\bADMINISTRATION\b.*",str(ET.tostring(child).decode("utf-8")),re.IGNORECASE | re.DOTALL)\
                and len(dosText)==0:
                    isDosage=1
            
            if isIndication==1 and child.tag!="code":
                if ET.fromstring(section).find("text")!=None:
                    for text in ET.fromstring(section).findall("./text"):
                        indicTitles.append("")
                        indicText.append(str(BeautifulSoup(ET.tostring(text).decode("utf-8"),"html.parser")))
                elif child.tag=="text":
                    indicTitles.append("")
                    indicText.append(str(BeautifulSoup(ET.tostring(child).decode("utf-8"),"html.parser")))
                    
                for comp in find_rec(ET.fromstring(section),"./component/section"):
                    indTx=""
                    indTl=""
                    for c in comp.findall("./title"):
                        indTl = str(BeautifulSoup(ET.tostring(c).decode("utf-8"),"html.parser"))
                    
                    for c in comp.findall("./text"):
                        indTx = indTx+str(BeautifulSoup(ET.tostring(c).decode("utf-8"),"html.parser"))
                       
                    if re.match(".*(?:limitations|contraindication|efficacy|concentrations).*",indTl,re.IGNORECASE | re.DOTALL)==None:
                        indicTitles.append(indTl)
                        indicText.append(indTx)
                
                
            
            if isDosage==1 and child.tag!="code":
                if ET.fromstring(section).find("text")!=None:
                    for txt in ET.fromstring(section).findall("./text"):
                        dosTitles.append("")
                        dosText.append(str(BeautifulSoup(ET.tostring(txt).decode("utf-8"),"html.parser")))
                elif child.tag=="text":
                    dosTitles.append("")
                    dosText.append(str(BeautifulSoup(ET.tostring(child).decode("utf-8"),"html.parser")))
                    
                for cmp in find_rec(ET.fromstring(section),"./component/section"):
                    dosTx=""
                    dosTl=""
                    for dc in cmp.findall("./title"):
                        dosTl=str(BeautifulSoup(ET.tostring(dc).decode("utf-8"),"html.parser"))
                    for dc in cmp.findall("./text"):
                        dosTx = dosTx+str(BeautifulSoup(ET.tostring(dc).decode("utf-8"),"html.parser"))
                    if re.match(".*(?:limitations|contraindication|efficacy|concentrations).*",dosTl,re.IGNORECASE | re.DOTALL)==None:
                            dosTitles.append(dosTl)
                            dosText.append(dosTx)
                

            if isIndication==1 and len(indicText)>0:
               isIndication=0 
            
            if isDosage==1 and len(dosText)>0:
               isDosage=0 
              
        for NDC in re.findall(r'.* code="[\d]{4,5}-[\d]{3,4}-[\d]{1,2}".*',str(section),re.IGNORECASE,re.MULTILINE):
            #print(ET.fromstring(NDC).attrib['code'])
            ndc=str(ET.fromstring(NDC).attrib['code'])
            ndcL=ndc.split("-")
            ndcALL.add("-".join([ndcL[0].zfill(5),ndcL[1].zfill(4)]))
        
        PNameStart=section.find("<name>")
        PNameEnd=section.find("</name>",PNameStart)
        if PNameStart>-1:
            ProductName.add(str(section[PNameStart+6:PNameEnd]))
            
        GenericStart=section.find("<genericMedicine>")
        GenericEnd=section.find("</genericMedicine>",GenericStart)
        if GenericStart>0: GenericString=section[GenericStart+17:GenericEnd]
        for node in ET.fromstring(GenericString).iter():
            if node.tag=="name": MoleculeName.add(str(node.text.strip()))
        
        for node in ET.fromstring(section).iter():
            if node.tag=="formCode":
                MolDisplayName.add(str(node.attrib['displayName']))
        
        
        #print(section[PNameStart+6:PNameEnd])
    
    #nodestart=[i for i, letter in enumerate(indication) if letter == "<"]
    #nodeend=[i for i, letter in enumerate(indication) if letter == ">"]
# =============================================================================
#     Tcontent=[]
#     for dos in dosText:
#         for table in ET.fromstring(dos).findall('./table'):
#             for row in table.getchildren():
#                 if row.tag=="caption":
#                     Tcap=row.text
#             print(Tcap)
#             for index,tbody in enumerate(table.findall('./tbody/tr')):
#                 if index==0:
#                     heads=[tr.text for tr in tbody.iter() if tr.text!=None]
#                 elif index==1:
#                     subhead=[td.text for td in [tr for tr in tbody.iter() if tr.text!=None and  'stylecode' in tr.attrib] if td.attrib['stylecode'] =="bold"]
#                 else:
#                     Tcontent.append([ET.tostring(tr).decode("utf-8") for tr in tbody.iter() if tr.text!=None])
#                 
#             print(heads)
#             print(subhead)
#             print(Tcontent)
# =============================================================================
    
    for n,i in enumerate(indicText):
        if re.search(r"<table.*table>",i,re.IGNORECASE | re.DOTALL)!=None:
            i=i.replace(re.search(r"<table.*table>",i,re.IGNORECASE | re.DOTALL).group(),"")
        if i !="":
            for para in ET.fromstring(i).iter():
                if para.tag=="content" and "stylecode" in para.attrib:
                    if para.attrib['stylecode'] in ['italics','bold','underline']:
                            i=i.replace(str(BeautifulSoup(ET.tostring(para).decode("utf-8"),"html.parser")),"*"+str(BeautifulSoup(ET.tostring(para).decode("utf-8"),"html.parser")).strip()+':')
                if para.tag=="item":
                    if para.text !=None:
                        i=i.replace(para.text,"*"+para.text)
                    else:
                        i=i.replace(str(BeautifulSoup(ET.tostring(para).decode("utf-8"),"html.parser")),"*"+str(BeautifulSoup(ET.tostring(para).decode("utf-8"),"html.parser")).strip())
        indicText[n]=i
        
    indicTemp=[re.findall(r"(?:<paragraph.*?paragraph>|(?:/*|)<item.*?item>)",i,re.I | re.DOTALL) for i in indicText]
    c=[i for i in indicTemp if i==[]]
    if len(indicTemp)==len(c):
        indicText = [i.split("\n") for i in indicText]
    else:
        indicText=indicTemp

            
# =============================================================================
#         for table in re.findall(r"<table.*?table>",i,re.IGNORECASE | re.DOTALL):
#             tdListoList=[]
#             tableText=""
#             thList=[] 
#             tabType=1
#             
#             for td in ET.fromstring(table).findall("./thead/tr/td"):
#                 thList.append(re.sub(r"<.*?>","",str(BeautifulSoup(ET.tostring(td).decode("utf-8"),"html.parser"))).replace("\n"," "))
#             
#             for r,tr in enumerate(ET.fromstring(table).findall("./tbody/tr")):  
#                 tdList=list()
#                 for th in tr.findall("./td"):
#                     if r==0 and len(thList)==0:
#                         thList.append(re.sub(r"<.*?>","",str(BeautifulSoup(ET.tostring(th).decode("utf-8"),"html.parser"))).replace("\n"," "))
#                         if len(thList)>0:
#                             if thList[0].strip()=="":
#                                 tabType=2
#                     else:
#                         tdList.append(re.sub(r"<.*?>","",str(BeautifulSoup(ET.tostring(th).decode("utf-8"),"html.parser"))).replace("\n"," "))
#                         
#                 tdListoList.append(tdList)
#                 tdListoList=list(filter(None,tdListoList))
#                 
#             #thList=RemoveXMLTagsTitles(thList)
#             #tdListoList=RemoveXMLTags(tdListoList)
#             if tabType==1:
#                 for j in tdListoList:
#                     tableText="*"+tableText+"\n".join([h+":"+r for h,r in zip(thList,j)])+"\n"
#             elif tabType==2 and len(tdListoList)>0:
#                 tdListoList=list(Transpose(tdListoList))
#                 
#                 if len(thList)<=len(tdListoList):
#                     for k,j in enumerate(thList):
#                         if k==0:
#                             sH=tdListoList[k]
#                         else:
#                             tableText=tableText+j+"$"+",".join(["*"+sh+":"+r for sh,r in zip(sH,tdListoList[k])])+"\n"
#             
#             #print(dosText[n].replace(table,tableText))
#             tableText=r"<paragraph>"+tableText+r"</paragraph>"
#             tablereplace=re.compile(r"<table.*?table>",re.IGNORECASE | re.DOTALL)
#             dosText[n]=tablereplace.sub(tableText,i)
# =============================================================================
        
    for n,i in enumerate(dosText):
# =============================================================================
#         if re.search(r"<table.*table>",i,re.IGNORECASE | re.DOTALL)!=None:
#             print(re.search(r"<table.*table>",i,re.IGNORECASE | re.DOTALL).group())
#             i=i.replace(re.search(r"<table.*table>",i,re.IGNORECASE | re.DOTALL).group(),"")
# =============================================================================
        if i !="":
            for para in ET.fromstring(i).iter():
                if para.tag=="content" and "stylecode" in para.attrib:
                    if para.attrib['stylecode'] in ['italics','bold','underline']:
                        i=i.replace(str(BeautifulSoup(ET.tostring(para).decode("utf-8"),"html.parser")),"*"+str(BeautifulSoup(ET.tostring(para).decode("utf-8"),"html.parser")).strip()+':')
                if para.tag=="item":
                    if para.text !=None:
                        i=i.replace(para.text,"*"+para.text)
                    else:
                        i=i.replace(str(BeautifulSoup(ET.tostring(para).decode("utf-8"),"html.parser")),"*"+str(BeautifulSoup(ET.tostring(para).decode("utf-8"),"html.parser")).strip())
        dosText[n]=i    
    
    dosTemp=[re.findall(r"(?:<paragraph.*?paragraph>|(?:/*|)<item.*?item>|<table.*?table>)",i,re.I | re.DOTALL) for i in dosText]
    
    c=[i for i in dosTemp if i==[]]
    if len(dosTemp)==len(c):
        dosText = [i.split("\n") for i in dosText]
    else:
        dosText=dosTemp
    
    """Remove html tags and convert everything in plain text"""
    indicText = RemoveXMLTags(indicText)
    dosText = RemoveXMLTags(dosText)
    indicTitles = RemoveXMLTagsTitles(indicTitles)
    dosTitles = RemoveXMLTagsTitles(dosTitles)
    IndicationList=[]
    
    #re.split("(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s",indic) sentence division regex
    for i,indicL in enumerate(indicText):
        isList=False
        if len(indicL)>0:
            if indicL[0].endswith(":"):
                isList=True
        indicList=list(indicL)
        Temp=[]
        for j,indic in enumerate(indicL):
            indic=indic.strip()
            if isList==True and j!=0:
                indic="*"+indic
            
            indicTemp="\n".join([extractIndicSent(sent) for sent in nltk.sent_tokenize(indic) ])
            
                
            if indicTemp.strip()=='' and re.match(r"[\W\d].*",indic)!=None and re.match(r".*\bnot\W*\bindicated\b.*",indic,re.IGNORECASE | re.DOTALL)==None:
            #and re.match(".*(?:limitations|contraindication|efficacy|concentrations).*",indic,re.IGNORECASE | re.DOTALL)==None
                indic=indic.strip().lstrip('0123456789.- *')
                #indic=indic.replace(r"*","")
                if re.match(r".*\b(?:INDICATION|INDICATIONS)\b.*\bsection\b.*",indic,re.IGNORECASE | re.DOTALL)!=None:
                    indic=""
                if len(indic)>1:
                    indic=indic[0].upper()+indic[1:]
                if indic.endswith(':'):
                    indic='$ '+indic
                else:
                    indic='•'+indic
            elif j!=0 and indicTemp.strip()=='' and indicText[i][j-1].strip().endswith(':'):
                indic="\n".join(['o '+sent.strip() for sent in nltk.sent_tokenize(indic) if re.match(r".*(linkhtml).*",sent,re.IGNORECASE | re.DOTALL)==None] ) 
            else:
                indic=indicTemp
           
                
            indic=re.sub(r"\n+",'\n',indic)
            indic=indic.replace(r"*","")
            
            indicText[i][j]=indic.strip()
        indicText[i]=list(filter(None,indicText[i]))
        if indicText[i]==[]:
            indicText[i]=["\n".join(['•'+sent.strip() for sent in nltk.sent_tokenize("\n".join(indicList)) if re.match(r".*(linkhtml).*",sent,re.IGNORECASE | re.DOTALL)==None] )]
        #IndicationList.append("\n".join(Temp))
    IndicationList=indicText
    
    #IndicationList = [[re.search(r"(?:\bnot|)\W*\bindicated\b.*",sent,re.IGNORECASE | re.DOTALL).group().strip().capitalize() for sent in IndSentences if re.match(r".*(?:\bnot|)\W*\bindicated\b.*",sent,re.IGNORECASE | re.DOTALL)] \
    #                        for IndSentences in [re.split("(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s",indic) for indic in [indic for indic in [i for i in indicText]]]]

# =============================================================================
#     c=[i for i in IndicationList if len(i)==0]
#     if len(IndicationList)==len(c):
#         IndicationList = [[sent.strip() for sent in IndSentences] \
#                             for IndSentences in [re.split("(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s",indic) for indic in indicText]]
# =============================================================================
    #print(dosText)
    #dosTextCopy=list(list(dosText))
    
    dosTextCopy = list(map(list, dosText))
    
    for i,dosL in enumerate(dosText):
        Temp=[]
        for j,dos in enumerate(dosL):
            dos=dos.strip()
            if re.match(r"[\W\d].*",dos)!=None and re.match(r".*(?:\[|\().*?(?:see|See).*?(?:\]|\)).*",dos,re.IGNORECASE | re.DOTALL)==None:
                #dos=dos.strip().lstrip('0123456789.- ')
                if len(dos)>2:
                    dos=dos[0].upper()+dos[1:]
                if dos.endswith(':'):
                    dos='$ '+dos
                else:
                    dos='•'+dos
            elif j!=0 and dosText[i][j-1].endswith(':'):
                dos="\n".join(['o '+sent.strip() for sent in nltk.sent_tokenize(dos) if re.match(r".*(linkhtml).*",sent,re.IGNORECASE | re.DOTALL)==None\
                               and re.match(r".*(?:\[|\().*?(?:see|See).*?(?:\]|\)).*",sent,re.IGNORECASE | re.DOTALL)==None] )
            else:
                dos="\n".join(['o '+sent.strip() for sent in nltk.sent_tokenize(dos) \
                               if (dosFilter.match(sent) or dosFilterRto.match(sent) or re.match(r'.*\d.*%.*',sent, re.IGNORECASE | re.DOTALL)!=None)\
                               and re.match(r".*(linkhtml).*",sent,re.IGNORECASE | re.DOTALL)==None\
                               and re.match(r".*(?:\[|\().*?(?:see|See).*?(?:\]|\)).*",sent,re.IGNORECASE | re.DOTALL)==None] )
            
            dos=dos.replace(r"\n","")
            dos=dos.replace(r"*","")
            dosText[i][j]=dos
            
        dosText[i]=list(filter(None,dosText[i]))
        
        if dosText[i]==[]:
            dosText[i]=["\n".join(['o '+sent for sent in re.split("(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s","\n".join(dosTextCopy[i])) \
                   if re.match(r".*(linkhtml).*",sent,re.IGNORECASE | re.DOTALL)==None] )]
        #IndicationList.append("\n".join(Temp))
    DosageList=[]
    
    c=[i for i in dosText if i==[]]
    if len(dosText)==len(c):
        for dosL in dosTextCopy:
            DosageList.append(["\n".join([sent for sent in re.split("(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s","\n".join(dosL)) \
                                          if re.match(r".*(linkhtml).*",sent,re.IGNORECASE | re.DOTALL)==None])])
    else:
        DosageList=dosText
     
    
    for i,j in enumerate(IndicationList):
        for k,l in enumerate(j):
            if l in IndicationList[i][0:k-1] and k>0:
                IndicationList[i][k]=""
            if l.endswith("."):
                IndicationList[i][k]=IndicationList[i][k][:-1]
    
    
    
# =============================================================================
#     DosageList = [[sent.strip() for sent in dosSentences ] \
#                             for dosSentences in [re.split("(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s",dosg) for dosg in dosText]]
# =============================================================================
    if IndicationList!=[]:
        if re.sub(r"(?:[$o• ]\b|\W)","",IndicationList[0][0]).strip() in ["In","For","To","As"]:
            IndicationList[0][0]="$ Indicated "+re.sub(r"[$o• ]\b|\W","",IndicationList[0][0]).strip().lower()+":"
        
    if  len(indicTitles)!=0:
        for title,indications in zip(indicTitles,IndicationList):
            indications=[ind.strip() for ind in indications if ind.strip()!="" and re.match(r"NOTE:.*",ind,re.IGNORECASE | re.DOTALL)==None]
            title=re.sub(r"\s+"," ",title)
            title=title.strip().lstrip('0123456789.- ')
            title=re.sub(r"\w\.","",title)
            if title!="" and not title.endswith(':'): title=title+":" 
            if title!="": indication=indication+"$ "+title+ "".join(["\n"+i for i in indications if re.match(".*\w.*",i)!=None])+"\n"
            else: indication=indication+" "+ "\n".join([i for i in indications if re.match(".*\w.*",i)!=None])+"\n"
    else:
        for indications in IndicationList:
            indication=indication+"\n".join(indications)+"\n"
    
    
    #if re.match(r".*\bindicated\b.*",indication,re.IGNORECASE | re.DOTALL)==None:
    if IndicationList!=[]:
        if IndicationList[0][0].startswith("$ Indicated")==False:
            indication="Indicated: \n"+indication
    
    if  len(dosTitles)!=0:
        for title,dosages in zip(dosTitles,DosageList):
            dosages=[dos.strip() for dos in dosages if dos.strip()!="" and re.match(r"NOTE:.*",dos,re.IGNORECASE | re.DOTALL)==None]
            title=re.sub(r"\s+"," ",title)
            title=title.strip().lstrip('0123456789.- ')
            title=re.sub(r"\w\.","",title)
            if title!="" and not title.endswith(':'): title=title+":"
            if title!="": dosage=dosage+"$ "+title+ "".join(["\n"+d for d in dosages if re.match(".*\w.*",d)!=None])+"\n"
            else: dosage=dosage+"\n".join([d for d in dosages if re.match(".*\w.*",d)!=None])+"\n"
    else:
        for dosages in DosageList:
            dosage=dosage+"\n".join(dosages)+"\n"    
    
    
    for key in dosKeywords:
        if dosage.lower().find(key.lower()) !=-1:
            pos=dosage.lower().find(key.lower())
            dosage=dosage.replace(dosage[pos:pos+len(key)],'<b>'+dosage[pos:pos+len(key)]+'</b>')
        
# =============================================================================
#     for ndc in ndcALL:
#         cursor.execute("insert into xmlParseTest_kpl3(fileName,ProductName,MoleculeName,MolDisplayName,ndcALL,indication,dosage) "\
#                         "values(?,?,?,?,?,?,?);",
#                         (ntpath.basename(filepath),ProductName,MoleculeName,MolDisplayName,ndc,indication.strip(),dosage.strip()))
#         cursor.commit()
# =============================================================================
    
# =============================================================================
#     if ((indication.strip()=="")):
#         if ntpath.basename(filepath) in AcceptedFiles:
#             for ndc in ndcALL:
#                 open("E:/noindications.csv","a+").write(ndc+"\n")
# =============================================================================
    
    if len([mol for mol in MoleculeName if "Anticoagulant Citrate Phosphate" in mol])>0:
        indication="Indicated for Red Blood Cell preservation"
    if len(MoleculeName)==1 and list(MoleculeName)[0]=="Polyethylene Glycol 3350":
        indication="Indicated for the treatment of Occasional Constipation (irregularity)"
       
    ProductName= "|".join(ProductName)
    MoleculeName= "|".join(MoleculeName)
    MolDisplayName= "|".join(MolDisplayName)
    NDCs= "|".join(ndcALL)
    
    if re.match(r".*\b(?:helium|Carbon.*dioxide|Nitrogen)\b.*",MoleculeName,re.IGNORECASE)!=None:
        indication= "Not Available"
    elif re.match(r".*\bNitrous\b.*\boxide\b.*",MoleculeName,re.IGNORECASE)!=None:
        indication= "Indicated for anesthesia and analgesia in surgery"
    elif re.match(r".*\bOxygen\b.*",MoleculeName,re.IGNORECASE)!=None:
        indication= "Oxygen Supplement"
    elif re.match(r".*\bAir\b.*",MoleculeName,re.IGNORECASE)!=None:
        indication= "Breathing Support"
    
    if indication.strip()=="" and dosage.strip()!="":
        indication="\n".join(["o "+sent.replace("$","").replace(":","").strip() for sent in dosage.split("\n") if sent.strip().startswith("$")])
    elif indication.strip() in ["","Not Available"] and dosage.strip()=="":
        indication="Not Available"
        dosage="Not Available"
    
    dosage=re.sub(r"[:]\s*:",":",dosage)    
    
    if re.match(r".*(?:Allergenic extract|allergen).*",indication,re.IGNORECASE | re.DOTALL)==None:
        for ndc in ndcALL:
            if ndc not in IgnoreNDC:
                query="select APPLICATIONNUMBER,PRODUCTID,product_ndc,ProductCode,[code and ndc],[Product name],[company name], \
                                      [Product_Category],[molecule name],substance,form,Srength,Route_of_Administration,STARTMARKETINGDATE,\
                                      product_type,ENDMARKETINGDATE,PHARM_CLASSES,DEASCHEDULE,NDC_EXCLUDE_FLAG,\
                                      LISTING_RECORD_CERTIFIED_THROUGH from FDA_FINAL_TABLE where product_ndc="+"'"+str(ndc)+"'"
                for row in cursor.execute(query):
                    ExList.append([row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],\
                                   row[10],row[11],row[12],row[13],row[14],row[15],row[16],row[17],row[18],row[19],indication,dosage])

df = pd.DataFrame(ExList)
try:
    os.remove(r'F:\Pipeline\Source\InlinePipelineAutomatedLoad\Results\InlineOutput.xlsx')
except:
    pass
df.to_excel(r'F:\Pipeline\Source\InlinePipelineAutomatedLoad\Results\InlineOutput.xlsx', header=["APPLICATIONNUMBER","PRODUCTID","product_ndc","ProductCode","code and ndc","Product name","company name", \
                                      "Product_Category","molecule name","substance","form","Strength","Route_of_Administration","STARTMARKETINGDATE",\
                                      "product_type","ENDMARKETINGDATE","PHARM_CLASSES","DEASCHEDULE","NDC_EXCLUDE_FLAG",\
                                      "LISTING_RECORD_CERTIFIED_THROUGH","Indication","Dosage"], index=False)  


# =============================================================================
#     print("ProductName: "+ProductName)
#     print("MoleculeName: "+MoleculeName)
#     print("MolDisplayName: "+MolDisplayName)
#     print("NDCs: "+ NDCs)
#     print("indication: " + indication)
#     print("dosage: "+dosage)
# =============================================================================
#f.close()
#log.close()
#tempf.close()
