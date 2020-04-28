# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 15:45:51 2019

@author: Kapil.Gurjar
"""
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import pyodbc
from pathlib import Path
import datetime
import json
import dateparser
from Config import oltp_conn, dwh_conn, stg_db

starttime=datetime.datetime.now()

class load_forecast_pandas:
    
    def __init__(self,file_path):
        self.file_path=file_path
        self.oltp_db_config = "Driver={driver};\
        Server={server};\
        Database={db};\
        UID={user};\
        PWD={pwd};\
        Trusted_Connection={tc};".format(driver=oltp_conn['Driver'],server=oltp_conn['Server'],db=oltp_conn['Database'],user=oltp_conn['UID'],pwd=oltp_conn['PWD'],tc=oltp_conn['Trusted_Connection'])
        
        self.oltp=pyodbc.connect(self.oltp_db_config)

        #cursor_oltp=oltp.cursor()
        
        self.dwh_db_config = "Driver={driver};\
        Server={server};\
        Database={db};\
        UID={user};\
        PWD={pwd};\
        Trusted_Connection={tc};".format(driver=dwh_conn['Driver'],server=dwh_conn['Server'],db=dwh_conn['Database'],user=dwh_conn['UID'],pwd=dwh_conn['PWD'],tc=dwh_conn['Trusted_Connection'])
        self.dwh=pyodbc.connect(self.dwh_db_config)
        
        self.engine = create_engine("mssql+pyodbc://{user}:{pwd}@{server}/{db}?driver={driver}".format(user=dwh_conn['UID'],pwd=dwh_conn['PWD'],server=dwh_conn['Server'],db=dwh_conn['Database'],driver=dwh_conn['Driver'].strip('}').replace('{','').replace(" ","+")),echo=False)
        self.dimension_df=dict()

        
    def get_file_properties(self):
        path = Path(self.file_path)
        [self.tenant,self.model]=[path.parents[1].stem,path.parents[0].stem]
        
    
    def get_oltp_data(self):
        cursor_oltp=self.oltp.cursor()
        self.tenant_id = cursor_oltp.execute("select Id from dbo.TenantMaster where Name=?",(self.tenant.strip(),)).fetchone()[0]
        self.model_id = cursor_oltp.execute("select Id from byom.ModelMaster where Name=? and TenantId=?",(self.model.strip(),self.tenant_id,)).fetchone()[0]

        cursor_oltp.execute("select dm.Name,dm.dimensionTypeId from byom.DimensionSetMaster dm inner join byom.ModelDimensionSetMap mdm on \
                              dm.TenantId=mdm.TenantId and dm.Id=mdm.DimensionId where dm.TenantId=? and mdm.ModelId=?",(self.tenant_id,self.model_id,))

        self.dimension_list=[dict(name=row[0],
                                  type=row[1],
                                  column= (row[0]+"Id" if row[1]!=3 else row[0]),
                                  table= (row[0] if row[1]!=3 else None)) for row in cursor_oltp]

        cursor_oltp.execute("select mm.Name from byom.MeasureMaster mm inner join byom.ModelMeasureMap mmm on \
                              mm.TenantId=mmm.TenantId and mm.Id=mmm.MeasureId where mm.TenantId=? and mmm.ModelId=?",(self.tenant_id,self.model_id,))

        self.measure_list=[dict(name=row[0],table="_".join([row[0].replace(" ","_"),"Fact"])) for row in cursor_oltp]
    
    def extract(self):
        self.file_df = pd.read_csv(self.file_path)
        for dim in self.dimension_list:
            if dim["table"]:
                table_name=self.tenant+'."'+dim["table"]+'"'
                query="select Id, Name from "+table_name
                self.dimension_df[table_name]=pd.read_sql(query, con=self.engine)
    
    
    def transform(self):
        def convert_to_date(row):
            if type(row) is int:
                return datetime.datetime(1900, 1, 1) + datetime.timedelta(days=row)
            elif type(row) is str:
                return dateparser.parse(row,settings={'PREFER_DAY_OF_MONTH': 'first'})
            else:
                return row
        
        #udf_convert2date=udf(lambda x: convert_to_date(x),DateType())
        self.file_df['Value'] = self.file_df['Value'].astype('float')
        self.file_df['Forecast Date'] = self.file_df["Forecast Date"].apply(lambda x: convert_to_date(x))
        self.file_df= pd.pivot_table(self.file_df, values='Value',index=[dim['name'] for dim in self.dimension_list], columns=['KPI'],aggfunc=np.sum, fill_value=0).reset_index()
        self.file_df.reset_index(drop=True, inplace=True)
        
    def load_staging(self):
        for mes in self.measure_list:
            table_name = stg_db+".dbo."+"_".join([self.tenant,mes['table'],str(self.model_id)])
            column=[dim["name"] for dim in self.dimension_list]
            column.append(mes['name'])
            df_mes_tmp=self.file_df[column].copy()
            df_mes=df_mes_tmp[[mes['name']]].copy()
            
            for dim in self.dimension_list:
                if dim["table"]:
                    dim_tbl=self.tenant+'."'+dim["table"]+'"'
                    dim_df=self.dimension_df[dim_tbl]
                    df_mes[dim["column"]]=df_mes_tmp.merge(dim_df, how='left', left_on=[dim["name"]], right_on=['Name'])["Id"]
                else:
                    df_mes[dim["column"]]=df_mes_tmp[dim["name"]]
                
            df_mes.to_sql(table_name,con=self.engine,schema="STG",if_exists='replace',index=False,chunksize=100)
            
        
    def merge_main_table(self):
        
        cursor_dwh=self.dwh.cursor()
        cursor_dwh.execute("[dbo].[uspWarehouseStructure] ?,?,?,?",(self.tenant,self.model_id,json.dumps(self.dimension_list),json.dumps([mes["name"] for mes in self.measure_list]),))
        
        for mes in self.measure_list:
            stg_table_name=stg_db+".dbo."+"_".join([self.tenant,mes['table'],str(self.model_id)])
            table_name=self.tenant+"."+"_".join([mes['table'],str(self.model_id)])
            
            query="delete a from "+table_name+" a inner join "+stg_table_name+" b on "+" and ".join(["a.["+dim['name']+"Id]="+"b.["+dim['name']+"Id]" for dim in self.dimension_list if dim["type"]!=3])+" and "+" and ".join(["a.["+dim['name']+"]="+"b.["+dim['name']+"]" for dim in self.dimension_list if dim["type"]==3])
            cursor_dwh.execute(query)
    
            query_in="insert into "+table_name+"("+",".join(["["+dim['name']+"Id]" for dim in self.dimension_list if dim["type"]!=3])+","+",".join(["["+dim['name']+"]" for dim in self.dimension_list if dim["type"]==3])+",["+mes['name']+"]) select "+",".join(["["+dim['name']+"Id]" for dim in self.dimension_list if dim["type"]!=3])+","+",".join(["["+dim['name']+"]" for dim in self.dimension_list if dim["type"]==3])+",["+mes['name']+"]"+" from "+stg_table_name
            cursor_dwh.execute(query_in)
        
        cursor_dwh.commit()
        
    def main(self):
        self.get_file_properties()
        self.get_oltp_data()
        self.extract()
        self.transform()
        self.load_staging()
        self.merge_main_table()
        print("finished")
        
# =============================================================================
# if __name__=="__main__":
#     obj=load_forecast_spark()
#     obj.main()
# =============================================================================
