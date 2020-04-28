# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 16:11:43 2019

@author: Kapil.Gurjar
"""

import language_check
import pandas as pd
tool = language_check.LanguageTool('en-US')
from scipy import stats
from insights import insights
import numpy as np

class continuousSeries(insights):
    def setParameters(self,response):
        self.dimension=response.get('dimension','')
        self.measure=response.get('measure','')
        self.slices=response.get('slice',[])
        self.freq=response.get('freq','Year')
        self.significant_change=int(response.get('significantChange',20))
        self.df=pd.DataFrame(response['data'])
        self.df[self.measure] = self.df[self.measure].astype(float)
        self.df[self.dimension] = self.df[self.dimension].astype(np.datetime64)
    
    def getTrendingInsigths(self):  
        insights=[]
        if self.freq=='Month':
            form='%B, %Y'
            gr='CMGR'
        elif self.freq=='Quarter':
            form='%q, %Y'
            gr='CQGR'
        else:
            form='%Y'
            gr='CYGR'
        slope, intercept, r_value, p_value, std_err = stats.linregress(self.df.index, self.df[self.measure])
        if slope>0:
            trend='positive'
        else:
            trend='negative'


        min_max_trend=[]
        min_max_trend.append(list(self.df[[self.dimension,self.measure]].min()))
        min_max_trend.append(list(self.df[[self.dimension,self.measure]].max()))
        
        sent="".join(["The trend of "+self.measure+" forecast is "+trend+" with"," highest ($"+str(int(min_max_trend[1][1]))+") in "+(self.freq if self.freq!="Month" else "")+" " +min_max_trend[1][0].strftime(form)+" and lowest ($"+str(int(min_max_trend[0][1]))+") in "+(self.freq if self.freq!="Month" else "")+" "+min_max_trend[0][0].strftime(form)])
        insights.append(sent)
        
        f_val=self.df[self.df[self.dimension]==self.df[self.dimension].max()][self.measure].item()
        b_val=self.df[self.df[self.dimension]==self.df[self.dimension].min()][self.measure].item()

        if (f_val==0) and (b_val==0):
            cagr=0
        elif (f_val==0) and (b_val!=0):
            cagr=1
        else:
            cagr=(f_val/b_val)**(1/self.df[self.dimension].nunique())
            cagr=cagr-1
        
        insights.append("The linear trend of the forecast has R-squared value as "+str(round(r_value**2,2))+" and "+gr+" value as "+str(round(cagr*100,1))+"%")
        out_trend=pd.DataFrame(columns=["date","perct"])
        
        if trend=='positive':
            glitch=pd.DataFrame([{"date":self.df.iloc[i][self.dimension],"perct":int(-1*(b-a)*100//(a if a!=0 else 1))} for i, (a, b) in enumerate(zip(self.df[self.measure][::1], self.df[self.measure][1::1])) if ((b-a)<0) & (int(-1*(b-a)*100//(a if a!=0 else 1)>0))])
            out_trend=out_trend.append(glitch)
            drop_growth='drop'
        else:
            glitch=pd.DataFrame([{"date":self.df.iloc[i][self.dimension],"perct":int((b-a)*100//(a if a!=0 else 1))} for i, (a, b) in enumerate(zip(self.df[self.measure][::1], self.df[self.measure][1::1])) if ((b-a)>0) & (int((b-a)*100//(a if a!=0 else 1)>0))])
            out_trend=out_trend.append(glitch)
            drop_growth='growth'
        
        out_trend=out_trend.sort_values(by="perct",ascending=False).head(2)

        if out_trend.empty:
            insights.append("There is no "+drop_growth+" in "+self.measure+" forecast throughout the "+self.freq+"s ")
        else:
            for index,row in out_trend.iterrows():
                if row['perct']<=self.significant_change:
                    insights.append("There is a slight "+drop_growth+" of "+str(row['perct'])+"% in "+self.measure+" forecast in "+self.freq+" "+row['date'].strftime(form))
                else:
                    insights.append("There is a sudden "+drop_growth+" of "+str(row['perct'])+"% in "+self.measure+" forecast in "+self.freq+" "+row['date'].strftime(form))

        above_average=self.df[self.df[self.measure]>self.df[self.measure].mean()][self.dimension]
        if above_average.count()>2:
            insights.append(self.measure+"  for "+str(above_average.count())+" "+(self.freq.lower() if self.freq.lower() else 'month')+"s have forecast above avergae "+self.measure+" ($"+str(int(self.df[self.measure].mean()))+")")


        return insights
    
    def getInsights(self):
        insights=self.getTrendingInsigths()
        return insights