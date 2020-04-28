# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 13:07:54 2019

@author: Kapil.Gurjar
"""

jdbc_url = "jdbc:sqlserver://192.168.100.14:1433;databaseName=Reporting_Warehouse;"

stg_db="Warehouse_Staging"


oltp_conn=dict()
oltp_conn['Driver']='{ODBC Driver 13 for SQL Server}'
oltp_conn['Server']='192.168.100.14'
oltp_conn['Database']='PaceMaster_Copy'
oltp_conn['UID']='sa'
oltp_conn['PWD']='admin@123'
oltp_conn['Trusted_Connection']='no'

dwh_conn=dict()
dwh_conn['Driver']='{ODBC Driver 13 for SQL Server}'
dwh_conn['Server']='192.168.100.14'
dwh_conn['Database']='Reporting_Warehouse'
dwh_conn['UID']='sa'
dwh_conn['PWD']='admin@123'
dwh_conn['Trusted_Connection']='no'