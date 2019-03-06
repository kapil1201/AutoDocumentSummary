reviewsneg = "H:/Webtext_Project/moviereviews/neg/"
reviewspos = "H:/Webtext_Project/moviereviews/pos/"
corpusNeg = Corpus(DirSource(reviewsneg))
corpusPos = Corpus(DirSource(reviewspos))
corpusNeg = tm_map(corpusNeg, removeWords, stopwords("english"))
corpusPos = tm_map(corpusPos, removeWords, stopwords("english"))
corpusNeg = tm_map(corpusNeg, removePunctuation)
corpusPos = tm_map(corpusPos, removePunctuation)
corpusNeg = tm_map(corpusNeg, removeNumbers)
corpusPos = tm_map(corpusPos, removeNumbers)
corpusNeg = tm_map(corpusNeg, content_transformer(tolower))
corpusPos = tm_map(corpusPos, content_transformer(tolower))
corpusNeg = tm_map(corpusNeg, stripWhitespace)
corpusPos = tm_map(corpusPos, stripWhitespace)
outdirNeg = "H:/Webtext_Project/moviereviews/cleanNeg/"
outdirPos = "H:/Webtext_Project/moviereviews/cleanPos/"
writeCorpus(corpusNeg, outdirNeg)
writeCorpus(corpusPos, outdirPos)

mydata <- read.csv(file="H:/Webtext_Project/moviereviews/cdb.csv", header=TRUE)
validation_index <- createDataPartition(mydata$class, p=0.80, list=FALSE)
Warning messages:
1: In createDataPartition(mydata, p = 0.8, list = FALSE) :
  Some classes have no records (  ) and these will be ignored
2: In createDataPartition(mydata, p = 0.8, list = FALSE) :
  Some classes have a single record (  ) and these will be selected for the sample
validation <- mydata[-validation_index,]
mydata <- mydata[validation_index,]

> mydata <- read.csv(file="H:/Webtext_Project/moviereviews/cdb.csv", header=TRUE)
> validation_index <- createDataPartition(mydata$class, p=0.50, list=FALSE)
> validation <- mydata[-validation_index,]
> mydata <- mydata[validation_index,]
> control <- trainControl(method="cv", number=10)
> metric <- "Accuracy"
> set.seed(7)
> fit.svm <- train(class~., data=mydata, method="svmRadial", metric=metric, trControl=control)

Attaching package: ‘kernlab’

The following object is masked from ‘package:ggplot2’:

    alpha

There were 50 or more warnings (use warnings() to see the first 50)
> 
