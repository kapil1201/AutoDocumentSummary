# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 15:45:51 2019

@author: Kapil.Gurjar
"""

from pyspark.sql import SparkSession
from pyspark import SparkConf, StorageLevel
from pyspark.sql.functions import input_file_name, udf
import pyodbc
from pathlib import Path
from pyspark.sql.types import FloatType,DateType
import datetime
import json
import dateparser
from Config import jdbc_url, oltp_conn, dwh_conn, stg_db

starttime=datetime.datetime.now()

class load_forecast_spark:
    
    def __init__(self,file_path):
        self.conf = SparkConf()
        #self.conf.set('spark.driver.extraClassPath', r'D:/spark-2.4.4-bin-hadoop2.7/jars/sqljdbc42.jar')
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

        #cursor_dwh=dwh.cursor()

        self.spark = SparkSession.builder.config('spark.driver.extraClassPath', r'D:/spark-2.4.4-bin-hadoop2.7/jars/sqljdbc42.jar').appName("Forecast.Reporting.ETL").getOrCreate()
    
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
        self.file_df = self.spark.read.format("com.databricks.spark.csv").option("header", "true").option("inferSchema", "true").load(r"D:\BYOM\ETL\files\pharma_Test\Model 1/Output_v_Before-Review.csv").persist(StorageLevel.MEMORY_AND_DISK)
        for dim in self.dimension_list:
            if dim["table"]:
                table_name=self.tenant+'."'+dim["table"]+'"'
                self.spark.read.format("jdbc")\
                .option("url", jdbc_url)\
                .option("dbtable", table_name)\
                .option("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver")\
                .option("user",dwh_conn['UID'])\
                .option("password",dwh_conn['PWD'])\
                .load().cache().createOrReplaceTempView("`"+dim["table"]+"`")
    
    
    def transform(self):
        def convert_to_date(row):
            if type(row) is int:
                return datetime.datetime(1900, 1, 1) + datetime.timedelta(days=row)
            elif type(row) is str:
                return dateparser.parse(row,settings={'PREFER_DAY_OF_MONTH': 'first'})
            else:
                return row
        
        udf_convert2date=udf(lambda x: convert_to_date(x),DateType())
        self.file_df = self.file_df.withColumn("Value",self.file_df["Value"].cast(FloatType()))
        self.file_df = self.file_df.withColumn("Forecast Date",udf_convert2date("Forecast Date"))
        
        pivot_df = self.file_df.groupby([dim['name'] for dim in self.dimension_list]).pivot('KPI').sum('Value')
        pivot_df.createOrReplaceTempView('denorm_tbl')
        
    def load_staging(self):
        for mes in self.measure_list:
            table_name = stg_db+".dbo."+"_".join([self.tenant,mes['table'],str(self.model_id)])
            column="`"+mes['name']+"`"
            desc_dim=""
            join_cond=""
            
            for dim in self.dimension_list:
                desc_dim= ",".join([desc_dim,"`"+dim['name']+"`"+".Id as `"+dim["column"]+"`" if dim["table"] else ""]).strip() if desc_dim else "`"+dim['column']+"`"
                if dim["table"]:
                    join_cond=" inner join ".join([join_cond,"`"+dim['table']+"`"+" on "+"`"+dim['table']+"`."+"name = t.`"+dim['name']+"`"]).strip() if join_cond else " inner join ".join(["`"+dim['table']+"`"+" on "+"`"+dim['table']+"`."+"name = t.`"+dim['name']+"`"])
                    
            join_query="select "+",".join([desc_dim.strip(),column.strip()])+" from "+" denorm_tbl as t inner join "+join_cond+" where "+column+" is not null"
            
            fact_df=self.spark.sql(join_query.strip())
            
            fact_df.write.format("jdbc")\
            .mode('overwrite')\
            .option("url", jdbc_url)\
            .option("user",dwh_conn['UID'])\
            .option("password",dwh_conn['PWD'])\
            .option("dbtable", table_name)\
            .option("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver")\
            .save()
        
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
        self.spark.stop()
        
if __name__=="__main__":
    obj=load_forecast_spark("D:\BYOM\ETL\files\pharma_Test\Model 1/Output_v_Before-Review.csv")
    obj.main()
