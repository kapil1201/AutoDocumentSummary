#import argparse
#from os.path import isfile

import re
import numpy as np
import tensorflow as tf

from docqa.data_processing.document_splitter import MergeParagraphs, TopTfIdf, ShallowOpenWebRanker, PreserveParagraphs
from docqa.data_processing.qa_training_data import ParagraphAndQuestion, ParagraphAndQuestionSpec
from docqa.data_processing.text_utils import NltkAndPunctTokenizer, NltkPlusStopWords
from docqa.doc_qa_models import ParagraphQuestionModel
from docqa.model_dir import ModelDir
from docqa.utils import flatten_iterable
from docqa.config import MODEL_DIR
import pandas as pd

"""
Script to run a model on user provided question/context document. 
This demonstrates how to use our document-pipeline on new input
"""


def main(Data: pd.DataFrame,nlp,model_dir,model):
    #parser = argparse.ArgumentParser(description="Run an ELMo model on user input")
    #parser.add_argument("model", help="Model directory")
    #parser.add_argument("question", help="Question to answer")
    #parser.add_argument("documents", help="List of text documents to answer the question with", nargs='+')
    #args = parser.parse_args()
    
    #print("Preprocessing...")

    # Load the model
    #model_dir = ModelDir(MODEL_DIR)
    #model = model_dir.get_model()
    print(model)
    if not isinstance(model, ParagraphQuestionModel):
        raise ValueError("This script is built to work for ParagraphQuestionModel models only")
    #print(model)
    # Read the documents
    documents = []
    documents.append(Data.at[0,'Filetext'])
    
    """import pyodbc

    conn = pyodbc.connect("Driver={ODBC Driver 13 for SQL Server};"               
               "Server=192.168.100.15;"
               "Database=PharmaAce;"
               "UID=sa;"
               "PWD=admin@123;"
               "Trusted_Connection=no;")

    cursor=conn.cursor()
#(23211,28690,33214,25638,25837,26454,28693,26137,31428,32087)

    for doc in cursor.execute("select cast(filetext as varchar(max)) as filetext from kpl_tmp"):
        documents.append(doc[0])
        #doc="D:\Document QnA\document-qa-master\Data\Drug_Delivery_Surveying_Global_Competitive_Landscape_BMI.txt"   
    if not isfile(doc):
        raise ValueError(doc + " does not exist")
    with open(doc, "r") as f:
        documents.append(f.read())
    """    
    #print("Loaded %d documents" % len(documents))
    #temp=documents[0].split()
    # Split documents into lists of paragraphs
    #documents=[" ".join(temp[i:(i+400)]) for i in range(1,len(temp),400)]
    documents = [re.split("\s*\n\s*", doc) for doc in documents]
    # Tokenize the input, the models expects data to be tokenized using `NltkAndPunctTokenizer`
    # Note the model expects case-sensitive input
    tokenizer = NltkAndPunctTokenizer()
    question = tokenizer.tokenize_paragraph_flat(Data.at[0,'Question'])  # List of words
    # Now list of document->paragraph->sentence->word
    documents = [[tokenizer.tokenize_paragraph(p) for p in doc] for doc in documents]
    
    # Now group the document into paragraphs, this returns `ExtractedParagraph` objects
    # that additionally remember the start/end token of the paragraph within the source document
    splitter = MergeParagraphs(400)
    #splitter = PreserveParagraphs() # Uncomment to use the natural paragraph grouping
    documents = [splitter.split(doc) for doc in documents]
    #print(str(len(documents))+" kpl") #kpl
    # Now select the top paragraphs using a `ParagraphFilter`
    print(len(documents)) #kpl
    if len(documents) == 1:
        # Use TF-IDF to select top paragraphs from the document
        selector = TopTfIdf(NltkPlusStopWords(True), n_to_select=5)
        context = selector.prune(question, documents[0])
    else:
        # Use a linear classifier to select top paragraphs among all the documents
        selector = ShallowOpenWebRanker(n_to_select=10)
        context = selector.prune(question, flatten_iterable(documents))
    
    #print("Select %d paragraph" % len(context))
    
    if model.preprocessor is not None:
        # Models are allowed to define an additional pre-processing step
        # This will turn the `ExtractedParagraph` objects back into simple lists of tokens
        context = [model.preprocessor.encode_text(question, x) for x in context]
    else:
        # Otherwise just use flattened text
        context = [flatten_iterable(x.text) for x in context]
    
    print("Setting up model")
    # Tell the model the batch size (can be None) and vocab to expect, This will load the
    # needed word vectors and fix the batch size to use when building the graph / encoding the input
    voc = set(question)
    for txt in context:
        voc.update(txt)
    model.set_input_spec(nlp,ParagraphAndQuestionSpec(batch_size=len(context)), voc)
    # Now we build the actual tensorflow graph, `best_span` and `conf` are
    # tensors holding the predicted span (inclusive) and confidence scores for each
    # element in the input batch, confidence scores being the pre-softmax logit for the span
    #print("Build tf graph") #kpl
    print("after set input spec")
    sess = tf.Session(config=tf.ConfigProto(allow_soft_placement=True))
    # We need to use sess.as_default when working with the cuNND stuff, since we need an active
    # session to figure out the # of parameters needed for each layer. The cpu-compatible models don't need this.
    with sess.as_default():
        # 8 means to limit the span to size 8 or less
        best_spans, conf = model.get_prediction().get_best_span(8)

    # Loads the saved weights
    model_dir.restore_checkpoint(sess)
    print("after loading weights")
    # Now the model is ready to run
    # The model takes input in the form of `ContextAndQuestion` objects, for example:
    data = [ParagraphAndQuestion(x, question, None, "user-question%d"%i)
            for i, x in enumerate(context)]

    #print("Starting run")
    # The model is run in two steps, first it "encodes" a batch of paragraph/context pairs
    # into numpy arrays, then we use `sess` to run the actual model get the predictions
    encoded = model.encode(data, is_train=True)  # batch of `ContextAndQuestion` -> feed_dict
    best_spans, conf = sess.run([best_spans, conf], feed_dict=encoded)  # feed_dict -> predictions
    
    best_para = np.argmax(conf)  # We get output for each paragraph, select the most-confident one to print
    
    #print("Best Paragraph: " + str(best_para))
    #print("Best span: " + str(best_spans[best_para]))
    #print("Answer text: " + " ".join(context[best_para][best_spans[best_para][0]:best_spans[best_para][1]+1]))
    #print("Confidence: " + str(conf[best_para]))
    
    return " ".join(context[best_para][best_spans[best_para][0]:best_spans[best_para][1]+1])


#if __name__ == "__main__":
#    main()