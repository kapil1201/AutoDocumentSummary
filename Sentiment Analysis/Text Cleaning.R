
R version 3.4.3 (2017-11-30) -- "Kite-Eating Tree"
Copyright (C) 2017 The R Foundation for Statistical Computing
Platform: x86_64-w64-mingw32/x64 (64-bit)

R is free software and comes with ABSOLUTELY NO WARRANTY.
You are welcome to redistribute it under certain conditions.
Type 'license()' or 'licence()' for distribution details.

  Natural language support but running in an English locale

R is a collaborative project with many contributors.
Type 'contributors()' for more information and
'citation()' on how to cite R or R packages in publications.

Type 'demo()' for some demos, 'help()' for on-line help, or
'help.start()' for an HTML browser interface to help.
Type 'q()' to quit R.

> library(tm)
Loading required package: NLP
> reviewsneg = "H:/Webtext_Project/moviereviews/neg/"
> reviewspos = "H:/Webtext_Project/moviereviews/pos/"
> corpusNeg = Corpus(DirSource(reviewsneg))
> corpusPos = Corpus(DirSource(reviewspos))
> corpusNeg = tm_map(corpusNeg, removeWords, stopwords("english"))
> corpusPos = tm_map(corpusPos, removeWords, stopwords("english"))
> corpusNeg = tm_map(corpusNeg, stripWhitespace)
> corpusPos = tm_map(corpusPos, stripWhitespace)
> corpusNeg = tm_map(corpusNeg, removePunctuation)
> corpusPos = tm_map(corpusPos, removePunctuation)
> corpusNeg = tm_map(corpusNeg, removeNumbers)
> corpusPos = tm_map(corpusPos, removeNumbers)
> corpusNeg = tm_map(corpusNeg, content_transformer(tolower))
> corpusPos = tm_map(corpusPos, content_transformer(tolower))
> outdirNeg = "H:/Webtext_Project/moviereviews/cleanNeg/"
> outdirPos = "H:/Webtext_Project/moviereviews/cleanPos/"
> writeCorpus(corpusNeg, outdirNeg)
> writeCorpus(corpusPos, outdirPos)
