# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 12:51:05 2019

@author: Kapil.Gurjar
"""

from ContinuousSlicedSeries import continuousSlicedSeries
from ContinuousSeries import continuousSeries

class objectFactory:
    def __init__(self,pattern):
        self.pattern=pattern
        
    def getObject(self):
        patternObjectMap={"continuousSeries":continuousSeries(),\
                          "continuousSlicedSeries":continuousSlicedSeries()
                         }
        
        return patternObjectMap.get(self.pattern,"NA")