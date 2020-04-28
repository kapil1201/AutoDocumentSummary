CREATE OR REPLACE PROCEDURE byom.uspGetReportChartData_Table_Copy
(TenantId int,  ModelList varchar(100),dimensionSet varchar(max),OutSetting varchar(max),MeasureSet varchar(max),rs_out INOUT refcursor) 
AS $$
declare Query1 nvarchar(max);
BEGIN


Query1='';
select TenantId=5;
select ModelList='[2]';
select dimensionSet='[{"item": ["1L","2L","3L"],"parent": "","dimension": "Line of Therapy","isAggregation":"0","parentdimension": "","children": {"dimension": "CYCLE","item": [{"item":["April Proj 2019"],"parent":"1L"}],"children": {"dimension": "CLASS","item": [{"item":["Obdivo","Yervoy"],"parent":"April Proj 2019"}]}}},{"item":[["2016-01-01","2016-01-31"],["2015-04-01","2015-06-30"],["2017-01-01","2017-12-31"],["2018-02-04","2019-08-10"]],"groupinterval":"1","isAggregation":"1","type":16,"partby":"MM","parent":"","dimension":"Forecast Date","parentdimension":"","children":{}}]';
select OutSetting='[{"dimension":"Class","order":"0","startIndex":3,"fetchCount":8},{"dimension":"Forecast Date","order":"2","startIndex":1,"fetchCount":2},{"dimension":"Line of Therapy","order":"3","startIndex":1,"fetchCount":1}]';
select MeasureSet='[{"name":"Patients","filter":null,"aggregation":"SUM(<P1>)","parameter":{"P1":"Patients"}}]';


Query1= udf_prepare_reporting_query(TenantId,ModelList,dimensionSet,OutSetting,MeasureSet);

--raise notice '%',Query1;
OPEN rs_out FOR EXECUTE Query1;

RETURN rs_out;

END;
$$ LANGUAGE plpgsql;

