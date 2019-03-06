mydata <- read.csv(file="H:/Webtext_Project/moviereviews/cdb.csv", header=TRUE, sep=",")
validation_index <- createDataPartition(mydata$class, p=0.80, list=FALSE)
validation <- mydata[-validation_index,]
mydata <- mydata[validation_index,]
control <- trainControl(method="cv", number=10)
metric <- "Accuracy"
set.seed(7)
fit.svm <- train(class~., data=mydata, method="svmRadial", metric=metric, trControl=control)
