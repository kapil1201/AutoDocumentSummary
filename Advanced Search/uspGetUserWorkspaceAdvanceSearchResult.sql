USE [PharmaACE]
GO
/****** Object:  StoredProcedure [dbo].[uspGetUserWorkspaceAdvanceSearchResult]    Script Date: 31-10-2018 17:49:42 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
ALTER PROC [dbo].[uspGetUserWorkspaceAdvanceSearchResult]
( 
 @searchText varchar(500),
 @userid int,
 @userRole int,
 @StartingIndex int,
 @ItemCount int,
 @AccessDateFrom datetime,
 @AccessDateTo datetime,
 @Sortby varchar(500),
 @FileTypeList varchar(200),
 @ProjectList varchar(200),
 @SharedWithUserList varchar(200),
 @TotalCount int=0 OUT,
 @DidYouMean varchar(500)='' OUT,
 @AnswerDoc int =0 OUT
)
AS
--select @ProjectList =null,
-- @FileTypeList =null,
-- @AccessDateFrom ='1970-01-01',
-- @AccessDateTo ='2018-08-23',
-- @SharedWithUserList =null,
-- @Sortby =0,
-- @searchText ='how many organizations in liaison with ISO, As of 2009',
-- @userid =30,
-- @userRole =3,
-- @StartingIndex =0,
-- @ItemCount =10

BEGIN
SET NOCOUNT ON
--select getdate(),'start...' --kpl
declare @initsearch varchar(100)
declare @searchTextStr varchar(2500)
declare @display varchar(100)
declare @BoldDisplay varchar(100)
declare @PatString varchar(100)
declare @PatString2 varchar(100)
declare @key varchar(100)
declare @Query nvarchar(max)
declare @isPhrase bit
declare @isScoreAvlbl bit=0
declare @isQuestion bit=0
DECLARE @QuestionSearch varchar(2500)

declare @phrases table (id int identity(1,1),phrase varchar(100))
declare @keyObjectMap table(objectId int,keyword varchar(100),isBold bit)
declare @specialchars table (item varchar(50))
declare @SharedWithUsers table (UserId int)
declare @QuestionWords table(word varchar(20))

select @DidYouMean = ''
select @initsearch = @searchText

if object_id('tempdb..#UserObjects') is not null
drop table #UserObjects
CREATE TABLE #UserObjects (ObjectID int)

SpellCheck:  --Label to come back after spell check

select @display=''
select @BoldDisplay=''
select @PatString=''
select @key=''
select @Query=''
select @isPhrase=0
select @isScoreAvlbl=0 

delete from @phrases
delete from @keyObjectMap
--delete from @specialchars
delete from @SharedWithUsers

if object_id('tempdb..#FilteredObjIds') is not null
drop table #FilteredObjIds
CREATE TABLE #FilteredObjIds (ObjectMasterId int, score varchar(100))

if object_id('tempdb..#InputKeywords') is not null
drop table #InputKeywords
CREATE TABLE #InputKeywords (ROW INT,keyword VARCHAR(1000),isPhrase bit)

if object_id('tempdb..#AllKeywords') is not null
drop table #AllKeywords
CREATE TABLE #AllKeywords (keyword varchar(100),display_term varchar(100),expression varchar(100),isSearchTerm bit)

if object_id('tempdb..#OutputData') is not null
drop table #OutputData
create table #OutputData (keyword varchar(100), ObjectMasterId int,fileText varchar(1200),CreatedDate datetime,Name varchar(200),Type int,Size decimal(30,10),Lineage varchar(200),FilePath varchar(500),score decimal(10,5))

/*Variables set Default to null*/
select @FileTypeList =nullif(@FileTypeList,'')
select @ProjectList =nullif(@ProjectList,'')
select @SharedWithUserList =nullif(@SharedWithUserList,'')


IF PATINDEX('%[A-Za-z0-1]%',@searchText)<>0 or @searchText='' --If input string has only special characters then return nothing
BEGIN
	IF @searchText<>@DidYouMean or @searchText='' --To identify the objectIds for user only once before spell check (no need after spell check)
	BEGIN
		INSERT INTO @specialchars(item) --getting all special characters, which are ignored by full text Contains search
		select '~'  as item union ALL
		select '`'  as item union ALL
		select '!'  as item union ALL
		select '@'  as item union ALL
		select '#'  as item union ALL
		select '$'  as item union ALL
		select '%'  as item union ALL
		select '^'  as item union ALL
		select '&'  as item union ALL
		select '+'  as item union ALL
		select '|'  as item union ALL
		select '*'  as item union ALL
		select '='  as item union ALL
		select '\'  as item union ALL
		select '{'  as item union ALL
		select '}'  as item union ALL
		select ':'  as item union ALL
		select ';'  as item union ALL
		select ','  as item union ALL
		select '<'  as item union ALL
		select '>'  as item union ALL
		select '/'  as item union ALL
		select '?'  as item union ALL
		select '['  as item UNION ALL
		select '*'  as item UNION ALL
		select '"'  as item UNION ALL
		select ']'  as item UNION ALL
		select '.'  as item
		
		INSERT INTO @QuestionWords(word) --getting all interrogative words to identify question
		select 'WHO'  as word union ALL
		select 'WHAT'  as word union ALL
		select 'WHEN'  as word union ALL
		select 'WHERE'  as word union ALL   
		select 'WHY'  as word union ALL
		select 'HOW'  as word union ALL
		select 'IS'  as word union ALL
		select 'CAN'  as word union ALL
		select 'DOES'  as word union ALL
		select 'DO'  as word union ALL
		select 'WHICH'  as word union ALL
		select 'AM'  as word union ALL
		select 'ARE'  as word union ALL
		select 'WAS'  as word union ALL
		select 'WERE'  as word union ALL
		select 'MAY'  as word union ALL
		select 'MIGHT'  as word union ALL
		select 'CAN'  as word union ALL
		select 'COULD'  as word union ALL
		select 'WILL'  as word union ALL
		select 'SHALL'  as word union ALL
		select 'WOULD'  as word union ALL
		select 'SHOULD'  as word union ALL
		select 'HAS'  as word UNION ALL
		select 'HAVE'  as word UNION ALL
		select 'HAD'  as word UNION ALL
		select 'DID'  as word UNION ALL
		select 'WHOM'  as word UNION ALL
		select 'WHOSE'  as word 

		/*Identification of User accessible objectIDs (documents) starts*/
		insert into @SharedWithUsers
		select value from fnGetStringSeparated(@SharedWithUserList,',') where value<>@userid
		
		IF @userRole in (2,3) --Admin or SuperAdmin
		BEGIN
			/* 
			  If the login user is Admin or SuperAdmin then all the objects are accessible for the user, in case of SharedWith List selected by this user:
			   - SharedWith User can be a user, whom access of documents provided by sharing with her OR
			   - SharedWith User can be a BDL Lead, Owner or DealChampion of one or more projects, in this case all the objects of that project are accessible 
			     and should be fetched.
			*/
			;with cte as (select ROW_NUMBER()over (partition by ObjUserId order by modifiedDate desc) row,* from [ObjUserPermission] with(nolock))
			insert into #UserObjects(ObjectID)
			select DISTINCT ObjectId from [ObjectUserMapping] oum with(nolock)
			where (ShareWithId in (select UserId from @SharedWithUsers) OR @SharedWithUserList is null)
			AND Exists (select 1 from cte where ObjUserId=oum.Id and Permission<>9 and row=1)
		
			if @SharedWithUserList is not null
			begin
				;with cte as (select ROW_NUMBER()over (partition by objectid order by createddate desc) row,* from DealDetails with(nolock))
				insert into #UserObjects(ObjectID)
				select distinct om.Id
				from cte dd 
				inner join objectmaster om
				on charindex(cast(dd.ObjectID as varchar(10)),om.Lineage)<>0
				where (Owner in (select UserId from @SharedWithUsers) 
					 or BDL_Lead in (select UserId from @SharedWithUsers) 
					 or DealChampion in (select UserId from @SharedWithUsers)) and Type=2
				and row=1
			end
		END
		ELSE IF @userRole=1
		BEGIN
			if exists(select 1 from @SharedWithUsers)
			begin
			/* 
			  If the login user is not Admin or SuperAdmin, and SharedWith List selected by this user:
			   - SharedWith and Login User both can be users, whom access of documents provided by sharing with them
			   - Login user is normal user, whereas SharedWith User is a BDL Lead, Owner or DealChampion of one or more projects, 
			     in this case all the objects of that project, which are shared with Login user, are accessible and should be fetched.
			   - SharedWith user is normal user, whereas Login User is a BDL Lead, Owner or DealChampion of one or more projects, 
			     in this case all the objects of that project, which are shared with SharedWith User, are accessible and should be fetched.
			   - Both the users are BDL Leads, Owners or DealChampions of same projects, 
			     in this case all the objects of that project are accessible and should be fetched.
			*/
				;with cte as (select ROW_NUMBER()over (partition by objectid order by createddate desc) row,* from DealDetails with(nolock)),
				      cte2 as (select ROW_NUMBER()over (partition by ObjUserId order by modifiedDate desc) row,* from [ObjUserPermission] with(nolock))
				
				insert into #UserObjects(ObjectID)
				select X.objectId from
				(select distinct ObjectId,Id from [ObjectUserMapping] oum with(nolock)
				where shareWithId in (select userId from @SharedWithUsers) ) X
				inner join (select distinct ObjectId,Id  from [ObjectUserMapping] oum with(nolock)
				where shareWithId=@userid) Y
				on X.ObjectId=Y.ObjectId
				where Exists (select top 1 Permission from cte2 where ObjUserId=X.Id and Permission<>9 and row=1)
				
				union
				
				select distinct om.ObjectMasterId
				from cte dd 
				inner join UserWorkSpaceData om (nolock)
				on dd.ObjectID=om.ProjectID
				where (Owner in (select UserId from @SharedWithUsers) 
					 or BDL_Lead in (select UserId from @SharedWithUsers) 
					 or DealChampion in (select UserId from @SharedWithUsers))
				and (Owner = @userid 
					 or BDL_Lead = @userid
					 or DealChampion = @userid)
				and row=1 
		
				union
		
				select distinct om.ObjectMasterId
				from cte dd 
				inner join UserWorkSpaceData om (nolock)
				on dd.ObjectID=om.ProjectID
				inner join [ObjectUserMapping] oum 
				on om.ObjectMasterId=oum.ObjectId
				where (Owner in (select UserId from @SharedWithUsers) 
					 or BDL_Lead in (select UserId from @SharedWithUsers) 
					 or DealChampion in (select UserId from @SharedWithUsers))
				and shareWithId=@userid
				AND Exists (select top 1 Permission from cte2 where ObjUserId=oum.Id and Permission<>9 and row=1)
				and row=1 
		
				union
		
				select distinct om.ObjectMasterId
				from cte dd 
				inner join UserWorkSpaceData om (nolock)
				on dd.ObjectID=om.ProjectID
				inner join [ObjectUserMapping] oum 
				on om.ObjectMasterId=oum.ObjectId
				where (Owner =@userid
					 or BDL_Lead =@userid
					 or DealChampion =@userid)
				and shareWithId in (select UserId from @SharedWithUsers)
				AND Exists (select top 1 Permission from cte2 where ObjUserId=oum.Id and Permission<>9 and row=1)
				and row=1 
			end
			else
			begin
			/* 
			  If the login user is not Admin or SuperAdmin, and SharedWith List is not selected by this user:
			   - Fetch all the Objects, which are shared with this user OR
			   - Fetch all the documents of the projects for which this user is BDL Lead, DealChampion or Owner.
			*/
				;with cte as (select ROW_NUMBER()over (partition by ObjUserId order by modifiedDate desc) row,* from [ObjUserPermission] with(nolock))
				insert into #UserObjects(ObjectID)
				select distinct ObjectId from [ObjectUserMapping] oum with(nolock)
				where shareWithId =@userid 
				AND Exists (select top 1 Permission from cte where ObjUserId=oum.Id and Permission<>9 and row=1)
				
				;with cte as (select ROW_NUMBER()over (partition by objectid order by createddate desc) row,* from DealDetails with(nolock))
				insert into #UserObjects(ObjectID)
				select distinct om.ObjectMasterId
				from cte dd 
				inner join UserWorkSpaceData om with (nolock)
				on dd.ObjectID=om.ProjectID
				where (Owner=@userid or BDL_Lead=@userid or DealChampion=@userid) 
				and row=1 
			end
			
	END
END
/*Identification of User accessible objectIDs (documents) end*/
/*Check for Question or Information*/
IF len(@searchText)>=2
BEGIN
  IF LEFT(@searchText,1)<>'"' 
     AND (RIGHT(@searchText,1)='?' 
          OR EXISTS(SELECT 1 FROM @QuestionWords WHERE word= UPPER(SUBSTRING(@searchText,1,ISNULL(NULLIF(CHARINDEX(' ',@searchText),0),1)-1))))
  BEGIN
     SET @isQuestion=1
  END
END

/*Preparation of the Full text contains search string starts*/
/*Getting all the phrases from the input search string into @phrases table*/
;with cte as(select 
			 cast(substring(@searchText,charindex('"',@searchText),nullif(charindex('"',@searchText,charindex('"',@searchText)+1),0)-charindex('"',@searchText)+1) as varchar(200)) sub, 
			 charindex('"',@searchText,charindex('"',@searchText)+1) quote
			 
			 union all
			 
			 select 
			 cast(substring(@searchText,charindex('"',@searchText,quote+1),nullif(charindex('"',@searchText,charindex('"',@searchText,quote+1)+1),0)-quote-1) as varchar(200)) sub,
			 charindex('"',@searchText,charindex('"',@searchText,quote+1)+1) 
			 from cte where quote>0 and charindex('"',@searchText,quote+1)>0
			 )

insert into @phrases
select replace(sub,'"','') from cte where sub is not null

select @searchText = REPLACE(@searchText,phrase,'') from @phrases order by id --remove phrases from the search string, since these are not required for getting synonyms

select @searchText = replace(replace(REPLACE(@searchText,'()',''),')',' )'),'(','( ') --adding space to separate out brackets from keywords

update @phrases set phrase=LTRIM(RTRIM(phrase))

/*Insert all keywords separated by space into #InputKeywords table as rows*/
;with cte as(SELECT 1 row, CAST(LEFT(@searchText, CHARINDEX(' ', @searchText + ' ') - 1) AS VARCHAR(300)) AS Keyword
			 ,CAST(STUFF(@searchText, 1, CHARINDEX(' ', @searchText + ' '), '') AS VARCHAR(300)) AS Search
			 union all
			 SELECT row+1 row,CAST(LEFT(Search, CHARINDEX(' ', Search + ' ') - 1) AS VARCHAR(300)) AS Keyword
			,CAST(STUFF(Search, 1, CHARINDEX(' ', Search + ' '), '') AS VARCHAR(300)) AS Search FROM CTE
			 WHERE Search > ''
			 )
INSERT INTO #InputKeywords
select row,LTRIM(RTRIM(keyword)) keyword,0 as isPhrase from cte where keyword not in (' ')

/*Uniquely defining all the boolean operators to +, | and ~*/
UPDATE #InputKeywords SET keyword = CASE WHEN keyword in('AND','&') THEN '+' WHEN keyword = 'OR' THEN '|' WHEN keyword IN ('NOT','-') THEN '~' ELSE keyword END

/*Identifying the stops words to avoid checking synonyms for these words*/
delete tmp 
from #InputKeywords tmp
inner join dbo.StopWords sw
on sw.stopword=tmp.keyword

/*Removing the consecutive multiple boolean operators and keeping the first one only*/
;with cte as(select row_number() over(order by row) row,keyword from #InputKeywords )
delete c2 from cte c1 inner join cte c2 on c1.ROW+1=c2.ROW where c1.keyword in('+','~','|') and c2.keyword in('+','~','|')

/*Remove boolean from both the ends of string*/
;with cte as (select min(row) fkey,max(row) lkey from #InputKeywords)
delete tmp 
from #InputKeywords tmp
inner join cte on tmp.ROW=cte.fkey or tmp.ROW=lkey
where tmp.keyword in ('+','~','|')

/*Getting all the keywords (synonyms and stammers) to search and highlight in the snippet*/
insert into #AllKeywords
SELECT tmp.keyword, display_term, NULL AS EXPRESSION,0 isSearchTerm FROM #InputKeywords tmp cross apply sys.dm_fts_parser(N'FORMSOF(FREETEXT, "' + tmp.keyword + '")', 1033, 5, 0)  where expansion_type<>0
 and tmp.keyword not in ('|','+','~',')','(','""') 
 union 
 SELECT KEYWORD, KEYWORD, PREV_KEY AS EXPRESSION,0 isSearchTerm FROM
 (select keyword,LAG(keyword)OVER(ORDER BY ROW) PREV_KEY FROM #InputKeywords WHERE keyword NOT IN (')','(')) TMP
 where keyword not in ('|','+','~','""')

 --select getdate(),'before tmp update xml path' --kpl
 /*Updating the phrases back in the table to create the search string, since synonyms are identified*/
 ;with cte as(select row_number()over(order by getdate()) as row,keyword,isPhrase from #InputKeywords where keyword='""')
 update T set T.keyword=p.phrase,T.isPhrase=1
 from cte as T inner join @phrases p on T.row=p.id

 /*Replacing the keyword with a string of all the sysnonyms and stammers of the keyword in the full text acceptable format*/
update tmp
set tmp.Keyword = replace('("'+tmp.Keyword+ case when (isPhrase=0 or (isPhrase=1 and charindex(' ',tmp.Keyword)=0)) then '*"' else '"' end+isnull('|'+substring(A.List_Output,1,isnull(nullif(len(A.List_Output)-2,0),len(A.List_Output-1))),'')+')','''','''''


')
from 
 (
SELECT  row
       ,STUFF('"'+(SELECT CAST(words.display_term AS VARCHAR(100)) +'"|"'
         FROM #InputKeywords tmp inner join
		 #AllKeywords words
		 on tmp.row=main.row and tmp.keyword=words.keyword
		 where words.keyword<>words.display_term 
         FOR XML PATH(''), TYPE)
        .value('.','NVARCHAR(max)'),1,0,'') List_Output
FROM #InputKeywords main
where keyword not in ('|','+','~',')','(')
GROUP BY row) A inner join #InputKeywords tmp
on tmp.row=A.row

--select getdate(),'before #FilteredObjIds population' --kpl

SET @searchTextStr= (SELECT CAST(keyword AS VARCHAR(1000)) +'' --appending all the rows in one string to prepare search string
         FROM #InputKeywords 
         FOR XML PATH(''))

SET @QuestionSearch = REPLACE(@searchTextStr,')(',')&(')
SET @searchTextStr = REPLACE(@searchTextStr,')(',')|(')

SET @searchTextStr = REPLACE(REPLACE(@searchTextStr,')+(',')&('),')~(',')&!(') -- replacing back the boolean operators
/*Preparation of the Full text contains search string ends*/

/*Search and find the respective ObjectIds with the order starts*/

--Replace the sortby with the respective order by columns for ranking
SELECT @Sortby = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(@Sortby,'0','Score desc'),'1','CreatedDate desc'),'2','Name asc'),'3','Type asc'),'4','Size desc')

SELECT top 1 @isScoreAvlbl =  1 from documentscore where UserId=@userid

select @Query = ';with cte as (SELECT ObjectMasterId,dense_rank() over(order by '+isnull(@Sortby,'')+case when isnull(@Sortby,'')='' then '' else ',' end+' ObjectMasterId asc) as Score
		FROM UserWorkSpaceData usd with(nolock)
		left join documentscore ds with(nolock)
		on usd.ObjectMasterId = ds.objectId'
		+case when @isScoreAvlbl=1 then +' and ds.userid= '+cast(@userid as varchar(10)) else '' end +' 
		where ObjectMasterId in (select objectid from #UserObjects)
		'+case when @ProjectList is null then '' else 'AND usd.projectid in (select value from fnGetStringSeparated('''+@ProjectList+''','',''))' end
		 +case when @FileTypeList is null then '' else 'AND usd.Type in (select value from fnGetStringSeparated('''+@FileTypeList+''','',''))' end
		 +'AND usd.CreatedDate between CAST('''+CAST(@AccessDateFrom AS VARCHAR(20))+''' AS DATETIME) and CAST('''+CAST(@AccessDateTo AS VARCHAR(20))+''' AS DATETIME)'
		 +case when @searchTextStr IS NULL then '' else 'AND (contains(FileText,'''+@searchTextStr+''') or contains(Name,'''+@searchTextStr+'''))' end+')'+'
		  
	select distinct top '+cast(@ItemCount as varchar(10))+' ObjectMasterId,Score from cte where score between '+cast(@StartingIndex+1 as varchar(10))+' and '+cast((@StartingIndex+@ItemCount) as varchar(10))+' order by Score'

insert into #FilteredObjIds(ObjectMasterId,score)
EXEC SP_EXECUTESQL @Query

if @@rowcount=0 and @DidYouMean='' and @searchText<>''
begin
	declare @spellcheck table (ID int, Inkeyword varchar(100),Correct varchar(100))
	
	insert into @spellcheck
	EXEC [dbo].[uspPhraseCheck] @initsearch

	select @DidYouMean = @initsearch
	select @DidYouMean = replace(@DidYouMean,Inkeyword,Correct) from @spellcheck
	
	select @searchText = @DidYouMean

	goto SpellCheck;
end

IF @StartingIndex=0 --Getting the total objects count and assigning to output variable (only for the first page of search)
BEGIN
	IF isnull(@searchTextStr,'')=''
	BEGIN   
	        
			select @TotalCount = count(distinct ObjectMasterId) from UserWorkSpaceData usd with(nolock)
			where (usd.projectid in (select value from fnGetStringSeparated(@ProjectList,',')) OR @ProjectList is null)
			AND (usd.Type in (select value from fnGetStringSeparated(@FileTypeList,',')) OR @FileTypeList is null)
			AND usd.CreatedDate between @AccessDateFrom and @AccessDateTo
			and ObjectMasterId in (select objectid from #UserObjects)

			select @AnswerDoc=0
	END
	ELSE 
	BEGIN
	        --select @QuestionSearch --kpl
			
	        IF @isQuestion=1
			   select top 1 @AnswerDoc= ObjectMasterId from containstable (UserWorkSpaceData,Filetext,@QuestionSearch) tbl 
			   inner join UserWorkSpaceData usd on tbl.[key]=usd.ID
			   where (usd.projectid in (select value from fnGetStringSeparated(@ProjectList,',')) OR @ProjectList is null)
			   AND (usd.Type in (select value from fnGetStringSeparated(@FileTypeList,',')) OR @FileTypeList is null)
			   AND usd.CreatedDate between @AccessDateFrom and @AccessDateTo
			   and ObjectMasterId in (select objectid from #UserObjects)
			   and usd.[type] in (0, 1, 2, 23, 24, 25, 26, 28, 29, 37,9, 27)
			   order by [Rank] desc 
			ELSE
			   SET @AnswerDoc=0

			select @TotalCount = count(distinct ObjectMasterId) from UserWorkSpaceData usd with(nolock)
			where (usd.projectid in (select value from fnGetStringSeparated(@ProjectList,',')) OR @ProjectList is null)
			AND (usd.Type in (select value from fnGetStringSeparated(@FileTypeList,',')) OR @FileTypeList is null)
			AND usd.CreatedDate between @AccessDateFrom and @AccessDateTo
			and ObjectMasterId in (select objectid from #UserObjects)
			and (contains(FileText,@searchTextStr) or contains(Name,@searchTextStr))

	END
END

/*Search and find the respective ObjectIds with the order ends*/

--select getdate(),'before #AllKeywords delete population' --kpl

/*Get and Highlight the keywords in the output text starts*/
--Delete the keywords with NOT boolean operators to avoid for highlight search
DELETE T 
FROM #AllKeywords T inner join 
(select keyword 
 from #AllKeywords t2
 where t2.expression='~') X
ON X.keyword =T.keyword

--Identifying the actual input keyword, to first search for it
update #AllKeywords set isSearchTerm=1,display_term=display_term+'*' where keyword=display_term

--Keeping all the combination of Keywords and ObjectIds in a table to stop the search, once a keyword is found and highlighted
insert into @keyObjectMap
select distinct ObjectMasterId,keyword,0 isBold from #AllKeywords cross join #FilteredObjIds 

IF ISNULL(@searchTextStr,'')<>''
BEGIN
declare cur cursor for select display_term,keyword,isPhrase from
					  (select '"'+display_term+'"' as display_term,keyword,isSearchTerm,0 isPhrase from #AllKeywords 
					   union 
					   select '"'+phrase+'"',phrase,1 isSearchTerm,1 isPhrase from @phrases) X order by isSearchTerm desc
open cur
fetch next from cur into @display,@key,@isPhrase

while(@@FETCH_STATUS=0)
begin
	select @BoldDisplay=@display
	
	if @isPhrase=0 
	select @BoldDisplay = replace(@BoldDisplay,item,'') from @specialchars --removing the special characters from the keyword to highlight
	else
	select @BoldDisplay = replace(@BoldDisplay,'"','')

	select @PatString = '%[^a-z0-9]'+replace(replace(@display,'"',''),'*','')+'%'  --- pattern to find keyword which is a complete word (not a part of word) in the document
	select @PatString2 = '%[^a-z0-9]'+@BoldDisplay+'%'  --- pattern to find keyword which is a complete word (not a part of word) in the document

	insert into #OutputData
	select @key,usd.ObjectMasterId,
	case when PATINDEX(@PatString,fileText) <>0 
		 then replace(substring(FileText,PATINDEX(@PatString,fileText)-250,500),replace(replace(@display,'"',''),'*',''),'<em>'+replace(replace(@display,'"',''),'*','')+'</em>') 
	else replace(substring(FileText,PATINDEX(@PatString2,fileText)-250,500),@BoldDisplay,'<em>'+@BoldDisplay+'</em>') 
	end	 as fileText,
	CreatedDate,Name,Type,Size,Lineage,FilePath, score 
	from UserWorkSpaceData usd with (nolock)
	inner join #FilteredObjIds t3 on usd.ObjectMasterId = t3.ObjectMasterId
	where (contains(FileText,@display)) 
	and usd.ObjectMasterId not in (select ObjectId from @keyObjectMap where keyword=@key and isBold=1)
	order by score

	UPDATE kom SET kom.isBold=1 --updating the highlighted keyword to stop the search for same keyword's sysnonyms
	from @keyObjectMap kom inner join #OutputData t5  
	on t5.ObjectMasterId=kom.objectId and t5.keyword=kom.keyword
	where t5.keyword=@key

fetch next from cur into @display,@key,@isPhrase
end

close cur
deallocate cur
END
ELSE
BEGIN
	insert into #OutputData
	select '',usd.ObjectMasterId,
	LEFT(fileText,500) as fileText,
	CreatedDate,Name,Type,Size,Lineage,FilePath,score 
	from UserWorkSpaceData usd with (nolock)
	inner join #FilteredObjIds t3 on usd.ObjectMasterId = t3.ObjectMasterId
	order by score
END
--select getdate(),'after cursor' --kpl
END
/*Get and Highlight the keywords in the output text ends*/

--Getting only one snippet for one keyword and combining all the snippets of one object as the output
;with cte as (select row_number() over(partition by objectmasterid,keyword order by createddate desc) row,* from #OutputData (nolock)) 

SELECT  ObjectMasterId as UniqueId
       ,STUFF((SELECT CAST(tmp.fileText AS VARCHAR(max)) +'....'
         FROM cte tmp 
		 where tmp.ObjectMasterId=main.ObjectMasterId and row=1
         FOR XML PATH(''), TYPE)
        .value('.','NVARCHAR(max)'),1,0,' ') Excerpt,
		CreatedDate as CreationDate,Name as Title,Type as Extension,cast(Size/1024 as decimal(15,0)) as size,Lineage,FilePath as Path,null SharedWithUser
FROM cte main where row=1
GROUP BY ObjectMasterId,CreatedDate,Name,Type,Size,Lineage,FilePath,score
order by score


END

--TotalCount

--Creationdate
--FileText as Excerpt
--Extenstion as FileType
--Lineage
--FilePath as Path
--SharewithUSerList as sharedwithUser
--Size
--Name as Title
--ObjectMasterId as UniqueId




