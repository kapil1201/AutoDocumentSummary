# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 14:45:39 2019

@author: Kapil.Gurjar
"""

import pandas as pd
import numpy as np
from numpy.random import randint
import spacy

nlp=spacy.load("en_vectors_web_lg")

dimColName={'indication':['indication','disease'],'product':['product','drug','medication'],'company':['compnay','pharmaceutical'],'country':['country','location'],'region':['region','continent'],'scenario':['parameter','scenario','category','condition']}
dimData={'indication':['disease'],'product':['drug','medication'],'country':['country','location'],'company':['compnay','pharmaceutical'],'region':['region','continent']}

df=pd.read_csv(r"//192.168.100.14/data/BDL_DenormData.csv",encoding = "ISO-8859-1",nrows=50)

predMatrix=pd.DataFrame({'name':df.columns[0:6]})
predMatrix["predDim"] = ""
predMatrix["predValue"] = 0
for val in predMatrix.name:
    predName=""
    predVal=0
    for dimtype in dimColName:
        similarity=np.amax([nlp(val).similarity(nlp(word)) for word in dimColName[dimtype]])
        if similarity>predVal:
            predVal=similarity
            predName=dimtype
    print(predName)
    predMatrix.loc[predMatrix['name']==val,['predDim','predValue']]=[predName,predVal]
        #tmp.append(similarity)
print(predMatrix)  

scenario=['base','high','low']
for val in predMatrix.loc[(predMatrix['predDim']=="")|(predMatrix['predValue']<0.5),'name']:
    data=df[val][randint(1,50)]
    if data in scenario:
        predMatrix.loc[predMatrix['name']==val,['predDim','predValue']]=['scenario',1]
    else:
        predName=""
        predVal=0
        for dimtype in dimData:
            similarity=np.amax([nlp(data).similarity(nlp(word)) for word in dimData[dimtype]])
            if similarity>predVal:
                predVal=similarity
                predName=dimtype
        if predVal>0.3:
            predMatrix.loc[predMatrix['name']==val,['predDim','predValue']]=[predName,predVal]
    
print(predMatrix)
print(nlp('Young Plasma').similarity(nlp('medication')))

#dfCol=pd.DataFrame(dimColName)
#dfCol.head(2)
print(dimColName['indication'])
