from os.path import join, expanduser, dirname

"""
Global config options
"""
MODEL_DIR = join(dirname(dirname(__file__)),'models-cpu','squad')
DB_CONN="Driver={ODBC Driver 13 for SQL Server};Server=192.168.100.15;Database=PharmaAce_Dev;UID=sa;PWD=admin@123;Trusted_Connection=no;"
VEC_DIR = join("D:\Document QnA\python API testing", "data", "glove")
SQUAD_SOURCE_DIR = join(expanduser("~"), "data", "squad")
SQUAD_TRAIN = join(SQUAD_SOURCE_DIR, "train-v1.1.json")
SQUAD_DEV = join(SQUAD_SOURCE_DIR, "dev-v1.1.json")


TRIVIA_QA = join(expanduser("~"), "data", "triviaqa")
TRIVIA_QA_UNFILTERED = join(expanduser("~"), "data", "triviaqa-unfiltered")
LM_DIR = join(expanduser("~"), "data", "lm")
DOCUMENT_READER_DB = join(expanduser("~"), "data", "doc-rd", "docs.db")


CORPUS_DIR = join(dirname(dirname(__file__)), "data")
