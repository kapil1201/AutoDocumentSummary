> library(rnn)
> mydata <- read.csv(file="H:/Webtext_Project/moviereviews/cdb.csv", header=TRUE, sep=",")
> X1 = mydata$class[sample(900:1100,,replace=TRUE)]
> X2 = mydata$class[sample(800:1000,,replace=TRUE)]
> Y <- X1 + X2
> X1 <- int2bin(X1)
> X2 <- int2bin(X2)
> Y  <- int2bin(Y)
> X <- array( c(X1,X2), dim=c(dim(X1),2) )
> Y <- array( Y, dim=c(dim(Y),1) )
> model <- trainr(Y=Y[,dim(Y)[2]:1,,drop=F],X=X[,dim(X)[2]:1,,drop=F],learningrate = 0.1,hidden_dim = 10,batch_size = 200,numepochs = 10)
Trained epoch: 1 - Learning rate: 0.1
Epoch error: 4.67967983775737
Trained epoch: 2 - Learning rate: 0.1
Epoch error: 0.482587064676618
Trained epoch: 3 - Learning rate: 0.1
Epoch error: 0.482587064676618
Trained epoch: 4 - Learning rate: 0.1
Epoch error: 0.482587064676618
Trained epoch: 5 - Learning rate: 0.1
Epoch error: 0.482587064676618
Trained epoch: 6 - Learning rate: 0.1
Epoch error: 0.482587064676618
Trained epoch: 7 - Learning rate: 0.1
Epoch error: 0.482587064676618
Trained epoch: 8 - Learning rate: 0.1
Epoch error: 0.482587064676618
Trained epoch: 9 - Learning rate: 0.1
Epoch error: 0.482587064676618
Trained epoch: 10 - Learning rate: 0.1
Epoch error: 0.482587064676618
> plot(colMeans(model$error),type='l',xlab='epoch',ylab='errors')
> A1 = int2bin( mydata$class[sample(0:200,, replace=TRUE)] )
> A2 = int2bin( mydata$class[sample(1001:1201,, replace=TRUE)] )
> A <- array( c(A1,A2), dim=c(dim(A1),2) )
> B  <- predictr(model,A[,dim(A)[2]:1,,drop=F])
> B = B[,dim(B)[2]:1]
> A1 <- bin2int(A1)
> A2 <- bin2int(A2)
> B  <- bin2int(B)
> #plot difference
> hist( B-(A1+A2) )
Warning messages:
1: In A1 + A2 :
  longer object length is not a multiple of shorter object length
2: In B - (A1 + A2) :
  longer object length is not a multiple of shorter object length
> 