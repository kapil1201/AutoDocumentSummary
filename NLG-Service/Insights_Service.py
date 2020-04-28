# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 13:27:12 2019

@author: Kapil.Gurjar
"""

from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from ObjectFactory import objectFactory
import language_check
tool = language_check.LanguageTool('en-US')

app = Flask(__name__)
api = Api(app)

"""
post body example:
{"data":[{"Forecast Date":"2011-12-01","Class":"Class 1","Indication":"Indication 1","Net Revenue":0},{"Forecast Date":"2011-12-01","Class":"Class 1","Indication":"Indication 10","Net Revenue":0}],"pattern":"continuousSlicedSeries","freq":"Year","dimension":"Forecast Date","slice":["Indication","Class"],"measure":"Net Revenue","significantChange":"20"}    
"""
class Insights(Resource):
    def post(self):
        req = request.get_json()
        pattern=req.get("pattern",None)
        obj=objectFactory(pattern).getObject()
        
        obj.setParameters(req)
        insights=obj.getInsights()
        insights_correct=[language_check.correct(i, tool.check(i)) for i in insights]
        return jsonify(insights_correct)


api.add_resource(Insights, '/insights')


if __name__=="__main__":
    app.run(host='0.0.0.0')