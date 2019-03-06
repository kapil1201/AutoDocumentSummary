#import gzip
#import pickle
#from os.path import join, exists
from typing import Iterable, Optional

#import numpy as np

#from docqa.config import VEC_DIR

""" Loading words vectors """


def load_word_vectors(vec_name: str,nlp, vocab: Optional[Iterable[str]]=None, is_path=False):
    if vocab is not None:
        vocab = set(x.lower() for x in vocab)
    pruned_dict = {}
    #for word in vocab:
     #   open("E:/vocab2.txt","a+").write(word+"\n")
    for word in vocab:
        pruned_dict[word]=nlp(word).vector
    return pruned_dict

# =============================================================================
#     if not is_path:
#         vec_path = join(VEC_DIR, vec_name)
#     else:
#         vec_path = vec_name
#     if exists(vec_path + ".txt"):
#         vec_path = vec_path + ".txt"
#     elif exists(vec_path + ".txt.gz"):
#         vec_path = vec_path + ".txt.gz"
#     elif exists(vec_path + ".pkl"):
#         vec_path = vec_path + ".pkl"
#     else:
#         raise ValueError("No file found for vectors %s" % vec_name)
#     return load_word_vector_file(vec_path, vocab)
# 
# 
# def load_word_vector_file(vec_path: str, vocab: Optional[Iterable[str]] = None):
#     if vocab is not None:
#         vocab = set(x.lower() for x in vocab)
# 
#     # notes some of the large vec files produce utf-8 errors for some words, just skip them
#     if vec_path.endswith(".pkl"):
#         with open(vec_path, "rb") as f:
#             return pickle.load(f)
#     elif vec_path.endswith(".txt.gz"):
#         handle = lambda x: gzip.open(x, 'r', encoding='utf-8', errors='ignore')
#     else:
#         handle = lambda x: open(x, 'r', encoding='utf-8', errors='ignore')
#     #f=open("E:/word_vectors_2.txt","a+")
#     pruned_dict = {}
#     #for word in vocab:
#      #   open("E:/vocab2.txt","a+").write(word+"\n")
#     nlp=spacy.load("en_vectors_web_lg")
#     for word in vocab:
#         pruned_dict[word]=nlp(word).vector
# # =============================================================================
# #     with handle(vec_path) as fh:
# #         for line in fh:
# #             line=line.strip()
# #             word_ix = line.find(" ")
# #             word = line[:word_ix]
# #             if (vocab is None) or (word.lower() in vocab):
# #      #           f.write(line)
# #                 try:
# #                     pruned_dict[word] = np.array([float(x) for x in line[word_ix + 1:-1].split(" ")], dtype=np.float32)
# #                 except Exception as e: print(word+"  "+str(e))
# #     #f.close()
# # =============================================================================
#     return pruned_dict
# =============================================================================
