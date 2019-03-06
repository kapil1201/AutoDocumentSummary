# -*- coding: utf-8 -*-
"""
Created on Wed Oct 24 13:03:17 2018

@author: Kapil.Gurjar
"""

#!flask/bin/python
from flask import Flask
from flask import request
from flask_cors import CORS
from flask import jsonify
import spacy
import DocumentQA
app = Flask(__name__)
CORS(app)
nlp=spacy.load("en_vectors_web_lg")

@app.route('/docQA', methods=['POST'])

def post():
    
    print(request.is_json)
    content = request.get_json()
    #print(content)
    print(content['Question'])
    print(content['ObjectMasterId'])
    doc=DocumentQA.DocumentQA(content['Question'],content['ObjectMasterId'],nlp)
    Answer=doc.getAnswer()
    return jsonify(Answer)
app.run(host='0.0.0.0', port=5000)
