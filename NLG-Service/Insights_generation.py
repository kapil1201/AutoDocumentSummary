
import language_check
import numpy as np
import pandas as pd
from datetime import datetime
tool = language_check.LanguageTool('en-US')
import pyodbc

oltp_conn=dict()
oltp_conn['Driver']='{ODBC Driver 13 for SQL Server}'
oltp_conn['Server']='192.168.100.14'
oltp_conn['Database']='PaceMaster_Copy'
oltp_conn['UID']='sa'
oltp_conn['PWD']='admin@123'
oltp_conn['Trusted_Connection']='no'

oltp_db_config = "Driver={driver};Server={server};Database={db};UID={user};PWD={pwd};Trusted_Connection={tc};".format(driver=oltp_conn['Driver'],server=oltp_conn['Server'],db=oltp_conn['Database'],user=oltp_conn['UID'],pwd=oltp_conn['PWD'],tc=oltp_conn['Trusted_Connection'])
oltp=pyodbc.connect(oltp_db_config)

query='select DATEADD(yy, DATEDIFF(yy, 0, [Forecast Date]) - 1, 0) as [Forecast Date],product,indication,[Line of Therapy],sum([Net Revenue]) [Net Revenue] from [BYOM].[DenormReportingData_5_2] group by indication,[Line of Therapy],product,DATEADD(yy, DATEDIFF(yy, 0, [Forecast Date]) - 1, 0)'
#query='select product,sum([Net Revenue]) [Net Revenue] from [BYOM].[DenormReportingData_5_2] group by product'
starttime=datetime.now()
df=pd.read_sql(query,oltp)

date_dimension=['Forecast Date']
dimension=[col for col in df.select_dtypes(exclude=[np.float,np.datetime64]).columns if col!='Forecast Date']
measure=list(df.select_dtypes(include=[np.float]).columns)

dim_cnt=len(dimension)
dim_pairs=[]
if len(date_dimension)>0 and dim_cnt>1:
    for i in range(0,dim_cnt):
        for j in range(0,len(date_dimension)):
            dim_pairs.append([dimension[i],date_dimension[j]])
elif dim_cnt>1:
    for i in range(0,dim_cnt):
        for j in range(i+1,dim_cnt):
            dim_pairs.append([dimension[i],dimension[j]])

print(dim_pairs)
def getInsight(row,dim,mes):
    trend=""
    overall=round(compare_df.loc[compare_df[dim[1]]==row[dim[1]],'Avg_'+mes].item(),1)
    if overall>row[mes]:
        trend="less"
    else:
        trend="more"
    sent="For "+dim[0]+" "+str(row[dim[0]])+", "+str(row[dim[1]])+" generated proportionately "+trend+" "+mes+"("+str(round(row[mes],1))+"%) compared to other "+str(dim[0])+"s (overall: "+str(overall)+"%)"
    matches = tool.check(sent)
    if len(matches)>0:
        sent=language_check.correct(sent, matches)
    print(sent)


for mes in measure:
    newcol='_'.join(['Avg',mes])
    
    if dim_cnt==1:
        compare_df=df.copy()
        compare_df[newcol]=round(100*df[mes]/df[mes].sum(),1)
        compare_df.drop(mes,axis=1,inplace=True)
        
    for dim_pair in dim_pairs:
        required_df=pd.DataFrame()
        compare_df=pd.DataFrame()
        r_grpby=df.groupby(dim_pair)[mes].sum().to_frame(mes).sort_values(mes,ascending=False) #need to check the perfect place for sorting
        r_grpby=r_grpby.groupby(level=0).apply(lambda x: 100 * x / float(x.sum())).reset_index()
        
        if required_df.empty:
            required_df=r_grpby.copy()
        else:
            required_df=required_df.join(r_grpby,how='right')

        required_df=required_df.head(4) #should be ordered and selected top for all measures individually
        grpby=df.groupby(dim_pair[1])[mes].sum()
        if compare_df.empty:
            compare_df=grpby.to_frame(newcol).reset_index().copy()
        else:
            compare_df=compare_df.join(grpby.to_frame(newcol),how='right').reset_index()
        compare_df[newcol]=round(100*compare_df[newcol]/compare_df[newcol].sum(),1)
        required_df.apply(getInsight,axis=1,args=(dim_pair,mes))


#list(required_df.apply(getInsight,axis=1))

print(datetime.now()-starttime)

