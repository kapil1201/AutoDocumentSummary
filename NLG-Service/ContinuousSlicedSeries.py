# -*- coding: utf-8 -*-
"""
Created on Thu Oct 10 13:05:32 2019

@author: Kapil.Gurjar
"""

import pandas as pd
from scipy import stats
from num2words import num2words
from insights import insights
import numpy as np


class continuousSlicedSeries(insights):
    def setParameters(self,response):
        self.dimension=response.get('dimension','')
        self.measure=response.get('measure','')
        self.slices=response.get('slice',[])
        self.freq=response.get('freq','Year')
        self.significant_change=int(response.get('significantChange',20))
        self.df=pd.DataFrame(response['data'])
        self.df[self.measure] = self.df[self.measure].astype(float)
        self.df[self.dimension] = self.df[self.dimension].astype(np.datetime64)
        self.df_date=self.df.groupby(self.dimension)[self.measure].sum().to_frame(self.measure).reset_index()
        self.total_points=self.df_date[self.dimension].nunique()
    
    def getTrendingInsigths(self):
        form=""
        gr=""
        insights=[]
        reasons=[]
        
        if self.freq=='Month':
            form='%B, %Y'
            gr='CMGR'
        elif self.freq=='Quarter':
            form='%q, %Y'
            gr='CQGR'
        else:
            form='%Y'
            gr='CAGR'
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(self.df_date.index, self.df_date[self.measure])

        min_max_trend=[]
        min_max_trend.append(list(self.df_date.min()))
        min_max_trend.append(list(self.df_date.max()))

        sent="".join(["The trend of total "+self.measure+" forecast is "+('positive' if slope>0 else 'negative')+" with"," highest ($"+str(int(min_max_trend[1][1]))+") in "+(self.freq if self.freq!="Month" else "")+" " +min_max_trend[1][0].strftime(form)+" and lowest ($"+str(int(min_max_trend[0][1]))+") in "+(self.freq if self.freq!="Month" else "")+" "+min_max_trend[0][0].strftime(form)])
        insights.append(sent)
        
        f_val=self.df_date[self.df_date[self.dimension]==self.df_date[self.dimension].max()][self.measure].item()
        b_val=self.df_date[self.df_date[self.dimension]==self.df_date[self.dimension].min()][self.measure].item()

        if (f_val==0) and (b_val==0):
            cagr=0
        elif (f_val==0) and (b_val!=0):
            cagr=1
        else:
            cagr=(f_val/b_val)**(1/self.df_date[self.dimension].nunique())
            cagr=cagr-1

        insights.append("The average linear trend of the forecast has R-squared value as "+str(round(r_value**2,2))+" and "+gr+" value as "+str(round(cagr*100,1))+"%")

        out_trend=pd.DataFrame(columns=["date","perct"])
        
        if slope>0:
            glitch=pd.DataFrame([{"date":self.df.iloc[i][self.dimension],"perct":int(-1*(b-a)*100//(a if a!=0 else 1))} for i, (a, b) in enumerate(zip(self.df[self.measure][::1], self.df[self.measure][1::1])) if ((b-a)<0) & (int(-1*(b-a)*100//(a if a!=0 else 1)>0))])
            out_trend=out_trend.append(glitch)
            drop_growth='drop'
        else:
            glitch=pd.DataFrame([{"date":self.df.iloc[i][self.dimension],"perct":int((b-a)*100//(a if a!=0 else 1))} for i, (a, b) in enumerate(zip(self.df[self.measure][::1], self.df[self.measure][1::1])) if ((b-a)>0) & (int((b-a)*100//(a if a!=0 else 1)>0))])
            out_trend=out_trend.append(glitch)
            drop_growth='growth'
            
        out_trend=out_trend.sort_values(by="perct",ascending=False).head(1)
        
        if out_trend.empty==False:
            df_toDate= self.df[self.df[self.dimension]==out_trend.iloc[0]['date']]
            prev_date= self.df[self.df[self.dimension]<out_trend.iloc[0]['date']].sort_values(by=self.dimension,ascending=False).iloc[0][self.dimension]
            df_fromDate=self.df[self.df[self.dimension]==prev_date]
            
            df_details=df_toDate.merge(df_fromDate,how='outer',on=self.slices,suffixes=('_next','_prev'))
            df_details.loc[df_details[self.measure+'_next'].isna(),self.measure+'_next']=0
            df_details.loc[df_details[self.measure+'_prev'].isna(),self.measure+'_prev']=0
            df_details['diff']=df_details[self.measure+'_prev']-df_details[self.measure+'_next']
            df_details['diff']=(-1 if drop_growth=='growth' else 1)*df_details['diff']
            #df_details.sort_values(by='diff',ascending=False,inplace=True)
            
            #df_details[(df_details['diff']!=0) & (df_details[measure+'_next']==0)][slices]
        
            df_slices=pd.DataFrame(columns=['dim',self.measure+'_next',self.measure+'_prev','diff'])

            for slc in self.slices:
                df_slices=df_slices.append(df_details.groupby(slc).agg('sum').reset_index()[[slc,self.measure+'_next',self.measure+'_prev','diff']].rename(columns={slc:"dim"}),ignore_index=True)
    
            for index,row in df_slices.sort_values(by='diff',ascending=False).head(2).iterrows():
                if drop_growth=='drop':
                    if row[self.measure+'_next']==0:
                        reasons.append("absence of "+row['dim'])
                    else:
                        reasons.append("drop in "+row['dim']+"($"+str(int(row['diff']))+")")
                else:
                    if row[self.measure+'_prev']==0:
                        reasons.append("addition of "+row['dim'])
                    else:
                        reasons.append("growth in "+row['dim']+"($"+str(int(row['diff']))+")")

        for index,row in out_trend.iterrows():
            insights.append("There is a "+("slight" if row['perct']<=self.significant_change else "sudden")+" "+drop_growth+" of "+str(row['perct'])+"% in "+self.measure+" forecast in "+self.freq+" "+row['date'].strftime(form)+(", due to "+" and ".join(reasons) if len(reasons)>0 else ""))
        return insights
    
    def getSlicingInsights(self):
        
        insights_slc=[]
        for slc in self.slices:
            df_slc=self.df.groupby([slc,self.dimension]).agg('sum').reset_index()
            df_slc=df_slc.merge(pd.DataFrame(self.df_date[self.dimension].unique(),columns=[self.dimension]),how='right',on=self.dimension).sort_values(by=[slc,self.dimension],ascending=True)
            df_slc.loc[df_slc[self.measure].isna()][self.measure]=0
            df_slc[self.measure+'_prev']=df_slc.groupby(slc)[self.measure].shift(1)
            df_slc['diff']=df_slc[self.measure]-df_slc[self.measure+'_prev']
            df_slc_count=df_slc[df_slc[self.measure]!=0].groupby(slc).size().to_frame("count").reset_index()
            total_slc=df_slc[slc].nunique()
    
            if (df_slc_count['count'].count()==total_slc):
                size="all "
            elif (df_slc_count['count'].count()>total_slc//2):
                size=num2words(df_slc_count['count'].count())
            else:
                size="only "+num2words(df_slc_count['count'].count())
            insights_slc.append("Out of "+num2words(total_slc)+", "+size+" "+slc.lower()+"s are used for forecasting "+self.measure)
    
            if df_slc_count.max()['count']==self.total_points:
                sent=df_slc_count.max()[slc]+" is present throughout the "+self.freq+"s"
            else:
                sent=df_slc_count.max()[slc]+" is present in "+num2words(df_slc_count.max()['count'])+" "+self.freq+"s"
    
            slope, intercept, r_value, p_value, std_err = stats.linregress(df_slc[df_slc[slc]==df_slc_count.max()[slc]].index, df_slc[df_slc[slc]==df_slc_count.max()[slc]][self.measure])
            sent=sent+" with {} contribution in the forecast".format("increasing" if slope>0 else "decreasing")
            if df_slc_count.min()[slc]!=df_slc_count.max()[slc]:
                sent=sent+", whereas contribution of "+df_slc_count.min()[slc]+" is present in "+(num2words(df_slc_count.min()['count']) if df_slc_count.min()['count']>self.total_points//2 else "only "+num2words(df_slc_count.min()['count']))+" "+self.freq+"s"
            insights_slc.append(sent)
        return insights_slc
        
    def getInsights(self):
        insights=self.getTrendingInsigths()+self.getSlicingInsights()
        return insights


