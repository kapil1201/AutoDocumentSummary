# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 18:02:59 2019

@author: Kapil.Gurjar
"""
from abc import ABC, abstractmethod 

class insights(ABC): 
    
    @abstractmethod
    def setParameters(self,response):
        pass
    
    @abstractmethod
    def getInsights(self):
        pass
        
        
