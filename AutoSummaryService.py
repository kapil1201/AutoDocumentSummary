# -*- coding: utf-8 -*-
"""
Created on Wed Jan 30 19:29:29 2019

@author: Kapil.Gurjar
"""

from flask import Flask
from flask_cors import CORS
import GenerateSummary

app = Flask(__name__)
CORS(app)
@app.route('/DocSummary', methods=['POST'])

def post():
    GenerateSummary.GenerateSummary.GetSummary()
    return ""
app.run(host='0.0.0.0', port=5000)