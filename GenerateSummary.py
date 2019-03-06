from gensim.summarization import summarize
from gensim.summarization import keywords
import pyodbc
import regex as re
import nltk
from Configuration import DB_CONN

class GenerateSummary:
    @classmethod
    def GetSummary(self):
        
        sent_detector=nltk.data.load('tokenizers/punkt/english.pickle')

        conn = pyodbc.connect(DB_CONN)
        cursor=conn.cursor()
#(23211,28690,33214,25638,25837,26454,28693,26137,31428,32087)

# =============================================================================
# FileSum=[]
# 
# for file in glob(path.join(r"D:\Document Summary\Gensim Data\UserWorkSpace","*.{}".format("pdf"))):
#     file=r""+file
#     f=open(file,"rb")
#     print(file)
#     txt=[]
#     try: pdfReader = PyPDF2.PdfFileReader(f) 
#     except: continue
#     if pdfReader.isEncrypted:
#         pdfReader.decrypt('rosebud')
#     #print(pdfReader.getPage(1).extractText())
#     ft=open("D:\Document Summary\Gensim Data\Text.txt","w+")
#     fs=open("D:\Document Summary\Gensim Data\Summary.txt","w+")
#     text=""
#     
#     for i in range(1,pdfReader.numPages):
#         try:
#             text=text+'\n'+pdfReader.getPage(i).extractText()
#         except:
#             pass
#         if (i%10==0 or i==pdfReader.numPages):
#             #text=text.decode("utf-8")
#             #ft.write(text)
#             #ft.write("\n..................................\n")
#             summary=summarize(text, ratio=0.05)
#             if summary.lstrip().rstrip()=="":
#                 summary=summarize(text, ratio=0.1)
#             txt.append(summary)
#             #fs.write("{} : {}".format(i//10,summary))
#             #fs.write(summarize(text, ratio=0.1))
#             fs.write("\n..................................\n")
#             text=""
#             summary=""
#     FileSum.append([file,txt])
#     ft.close()
#     fs.close()
# =============================================================================

#open("E:\kapil.txt","w+").write(str(FileSum))

#print(txt)
#[open("D:\Document Summary\Gensim Data\Text.txt","a+").write(line) for line in txt]
#open("D:\Document Summary\Gensim Data\Summary.txt","w+").write(summarize(" \n".join(txt), ratio=0.01))

#25476 - problem with multiple lines and spaces between words
#26308
        r = re.compile(r"^\s+", re.MULTILINE)
        ReURL=re.compile("(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])?",re.IGNORECASE | re.DOTALL )
        FileSummary=[]
        ObjectList=[]
    #select distinct usd.objectmasterid from UserWorkSpaceData usd left join UserWorkSpaceDocSummary uss on usd.ObjectMasterId=uss.ObjectMasterId where uss.ObjectMasterId is null and type in (0,9,1,2)
        for row in cursor.execute("select distinct usd.objectmasterid from UserWorkSpaceData usd left join UserWorkSpaceDocSummary uss on usd.ObjectMasterId=uss.ObjectMasterId where uss.ObjectMasterId is null and type in (0,9,1,2)"):
           ObjectList.append(row[0])
        cursor.close()   

        for obj in ObjectList:
            filetext=""
            cursor2=conn.cursor()
            for file in cursor2.execute("select cast(filetext as varchar(max)) from UserWorkSpaceData where objectmasterid= ?",(obj)):
               filetext=filetext+file[0]
        
            paragraphs=filetext.split("\r\n")
            paragraphs = list(filter(None, paragraphs))
            MaxLength=(len(paragraphs)//50)+1
            MaxLength=max([MaxLength,50])
            paragraphs=[" ".join(paragraphs[k:MaxLength+k]) for k in range(0,len(paragraphs),MaxLength)]
    
    
            SummaryList=[]
            Keys=""
            for text in paragraphs:
                text=ReURL.sub("",text)
                text=r.sub("",text)
                text=" ".join(text.split())
        #sentences = sent_detector.tokenize(text.strip())
                summary=""
                i=0.01
       
                while (summary=="" and i<1):
                    summary=summarize(text, ratio=i)
                    i=i+0.05
       
                try:
                    keyword=keywords(text, ratio=0.01)
                except: pass
                Keys=Keys+keyword
                if summary is not None:
                    SummaryList.append(summary)
            FileSummary.append([obj,SummaryList,Keys])

        cursor=conn.cursor()    
        for obj,sumList,keyword in FileSummary:
            sumList = filter(None, sumList)
            if sumList is not None:
                try:
                    cursor.execute("insert into UserWorkSpaceDocSummary(ObjectMasterId,SummaryText,Keywords) "\
                               "values(?,?,?);",
                               (obj,"\n".join([sumy for sumy in sumList if sumy is not None]),",".join(keyword.split("\n"))))
                    cursor.commit()
                except Exception as e:
                    print(e)
                    cursor.rollback()
              
# =============================================================================
#    cursor2=conn2.cursor()
#    cursor2.execute("insert into UserWorkSpaceDocSummary(ObjectMasterId,SummaryText) "\
#                   "values(?,?);",
#                   (obj,"\n".join([str(index)+": "+sumy for index,sumy in enumerate(FileSummary[0][1])])))
#    
# cursor.commit()
# =============================================================================
   #open("E:/kapil.txt","w+").write("\n".join([str(index)+": "+sumy for index,sumy in enumerate(FileSummary[0][1])]))
       #[open("D:\Document Summary\Gensim Data\Comment.txt","a+").write(line) for line in sentences]
       #print(sentences)
       #print(len(RE_SENTENCE.findall(text)))
       #f=open("E:/kapil.txt","a+")
       #f.write(text)
       #f.write("\n....................................................\n")
       #f.write(summarize(text, ratio=0.01))
       #print ('Summary:')
       #print (summarize(text, ratio=0.01))
       #print ('\nKeywords:')
       #print (keywords(text, ratio=0.01))
       #f.close()
