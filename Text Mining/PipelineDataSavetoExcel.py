# -*- coding: utf-8 -*-
"""
Created on Tue Jan 29 12:12:36 2019

@author: Kapil.Gurjar
"""

import pyodbc
from bs4 import BeautifulSoup
import pandas as pd

DB_CONN="Driver={ODBC Driver 13 for SQL Server};Server=192.168.100.15;Database=Pipeline;UID=sa;PWD=admin@123;Trusted_Connection=no;"
#sent_detector=nltk.data.load('tokenizers/punkt/english.pickle')

conn = pyodbc.connect(DB_CONN)
cursor=conn.cursor()
ExList=[]
query="select [S.No],[NCT ID],[Product Name],[ Molecule Name],[intervention_type],[Company Name],[Indication],[Phase] from VIEW1_FINAL with(nolock)"
for row in cursor.execute(query):
    ExList.append([row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7]])

df = pd.DataFrame(ExList)
try:
    os.remove(r'F:\Pipeline\Source\InlinePipelineAutomatedLoad\Results\PipelineOutputView1.xlsx')
except:
    pass
df.to_excel('F:\Pipeline\Source\InlinePipelineAutomatedLoad\Results\PipelineOutputView1.xlsx', header=["S.No","NCT ID","Product Name"," Molecule Name","intervention_type","Company Name","Indication","Phase"], index=False)  
print("PipelineOutputView1.xlsx created")
ExList=[]
query="select [S.No],[NCT No.],[Phase],[Brief Title],[Indication And Code],[Interventions],[Interventions Description],[Sponsor/Collaborator],\
       [Expected Completion Date],[Countries],[Status] from VIEW2_FINAL with (nolock)"
for row in cursor.execute(query):
    ExList.append([row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10]])

df = pd.DataFrame(ExList)
try:
    os.remove(r'F:\Pipeline\Source\InlinePipelineAutomatedLoad\Results\PipelineOutputView2.xlsx')
except:
    pass
df.to_excel('F:\Pipeline\Source\InlinePipelineAutomatedLoad\Results\PipelineOutputView2.xlsx', header=["S.No","NCT No.","Phase","Brief Title","Indication And Code","Interventions","Interventions Description",\
                                      "Sponsor/Collaborator","Expected Completion Date","Countries","Status"], index=False)  
print("PipelineOutputView2.xlsx created")

ExList=[]
query="select [NCT NO.],[Start Date],[Primary Completion Date],[Official Title],[Brief Summary],[Detailed Description],[Study Design],[Primary Outcome],\
      [Secondary Outcome],[Study Arms],[Eligibility criteria],[Sex/Gender],[Ages] from VIEW3_FINAL with (nolock)"
for row in cursor.execute(query):
    ExList.append([row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12]])

df = pd.DataFrame(ExList)
try:
    os.remove(r'F:\Pipeline\Source\InlinePipelineAutomatedLoad\Results\PipelineOutputView3.xlsx')
except:
    pass
df.to_excel('F:\Pipeline\Source\InlinePipelineAutomatedLoad\Results\PipelineOutputView3.xlsx', header=["NCT NO.","Start Date","Primary Completion Date","Official Title","Brief Summary","Detailed Description","Study Design","Primary Outcome",\
                                      "Secondary Outcome","Study Arms","Eligibility criteria","Sex/Gender","Ages"], index=False)  
print("PipelineOutputView3.xlsx created")
