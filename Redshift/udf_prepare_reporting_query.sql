create or replace function udf_prepare_reporting_query(TenantId int,  ModelList nvarchar(100),dimensionSet nvarchar(max),OutSetting nvarchar(max),MeasureSet nvarchar(max))
 returns nvarchar(max)
stable
as $$
import json


ModelList=eval(ModelList)
dimensionSet=json.loads(dimensionSet)
MeasureSet=json.loads(MeasureSet)
OutSetting=json.loads(OutSetting)
Query=""
DimSelect=""
MesSelect=""

def find(key, dictionary):
    for k, v in dictionary.items():
        if k == key:
            yield v
        elif isinstance(v, dict):
            for result in find(key, v):
                yield result

dimListIn=[]
dimList=[]
dimListGr=[]

for d in dimensionSet:
    [dimListIn.append('"'+dim+'"') for dim in find('dimension',d) if dim!={}]
    
    if d.get('type',0)==16:
        dimList.append("t.FromDate as "+'"'+d['dimension']+'"')
        dimListGr.append("t.FromDate")
    else:
        dimList.append('"'+d['dimension']+'"')
        dimListGr.append('"'+d['dimension']+'"')
        
DimSelectIn=",".join(dimListIn)
DimSelect=",".join(dimList)
DimGroupby=",".join(dimListGr)

DimWhere=" and ".join(['("'+dim['dimension']+'" in ('+"'"+"','".join(dim['item'])+"'"+'))' for dim in dimensionSet if len(dim['item'])>0 and dim.get('type',0)!=16 and len(dim['children'])==0])

def parseChildren(json):
    rootItem = json.get('item',None)
    rootJson = json      
    output = []    
    query=""
    if(len(rootItem) > 0):
        for i in range(0,len(rootItem)):
            result = []
            element = rootItem[i]
            heirarchy=[]
            heirarchy.append("".join(['"',rootJson.get('dimension',None),'"',"='",element,"'"]))
            if(rootJson.get('children',None)):
                parseItem(rootJson.get('children',[]),element,heirarchy,result)
                if(len(result) > 0):
                    output.append(result)
                
        if(len(output) > 0):
            return output


def parseItem(childrenJson,childrenOf,heirarchy,result):
    dimension = childrenJson.get('dimension',None)
    item = childrenJson.get('item',[])
    children = childrenJson.get('children',{})
    if((children!={}) & (len(children.get('item',[]))>0) & (len(children.get('dimension',[])))>0):
        if(len(item) > 0):
            _flag = False
            for p in range(0,len(item)):
                if(item[p].get('parent',None) == childrenOf):
                    _flag = True
                    _item =item[p].get('item',None)
                    if(len(_item) > 0):
                        for i in range(0,len(_item)):
                            element = _item[i]
                            heirarchy.append("".join(['"',dimension,'"',"='",element,"'"]))
                            parseItem(children,element,heirarchy,result)
                            heirarchy=heirarchy[:-1]
            if(_flag!=True):
                result.append(heirarchy)
                return True
    else:
        if(len(item) > 0):
            flag = False
            for p in range(0,len(item)):
                if(item[p].get('parent',None) == childrenOf):
                    flag = True
                    _item =item[p].get('item',None)
                    if(len(_item) > 0):
                        heirarchy.append('"'+dimension+'"' + " in('" + "','".join(_item) + "')")
                        result.append(heirarchy)
                        return True                         
                if(flag!=True):
                    result.append(heirarchy)
                    return True

child_where=""
for dim in dimensionSet:
    if dim.get('children',{})!={}:
        child_where='('+") OR (".join([") OR (".join([" AND ".join(l2) for l2 in l1]) for l1 in parseChildren(dim)])+")"
        child_where="".join(["(",child_where,")"])
if len(DimWhere)>0:
    DimWhere=" AND ".join([DimWhere,child_where])
else:
    DimWhere=child_where

MesSelect=",".join([mes['aggregation'].replace('<P1>','"'+mes['parameter']['P1']+'"')+' as '+'"'+mes['name']+'"' for mes in MeasureSet])
MesSelectIn=",".join(['"'+mes['name']+'"' for mes in MeasureSet])
TableName="\nunion\n".join(['select '+','.join([DimSelectIn,MesSelectIn])+' from byom.DenormReportingData_'+str(TenantId)+'_'+str(mod) for mod in ModelList])

TimeDimQuery=""
JoinQuery=""
TimeDimQuery="".join(["\nunion all\n".join(["select "+"'"+dim.get('dimension',None)+"' as Dimension, "+"cast('"+i[0]+"' as datetime) as FromDate, "+"cast('"+i[1]+"' as datetime) as ToDate" for i in dim.get('item',[])]) for dim in dimensionSet if dim.get('type',0)==16])
JoinQuery=" AND ".join(['"'+dim['dimension']+'"'+" between t.FromDate and t.ToDate" for dim in dimensionSet if dim.get('type',0)==16])

if TimeDimQuery!="":
    TimeDimQuery="CREATE TABLE #TimeDimFilter(Dimension varchar(100), FromDate date, ToDate date);\n"+"insert into #TimeDimFilter\n"+TimeDimQuery+";"


Query=""
if TimeDimQuery=="":
    Query='select '+','.join([DimSelect,MesSelect])+' from ('+TableName+') X where '+DimWhere+' group by '+DimGroupby+';'
else:
    Query=TimeDimQuery+"\n"+'select '+','.join([DimSelect,MesSelect])+' from ('+TableName+') X inner join #TimeDimFilter t on '+JoinQuery+' where '+DimWhere+' group by '+DimGroupby+';'

return Query

$$ language plpythonu;