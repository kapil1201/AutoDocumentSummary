# -*- coding: utf-8 -*-
"""
Created on Mon Feb 18 20:20:01 2019

@author: Kapil.Gurjar
"""
import sys
import requests
import re
import urllib.robotparser as robotparser
import time
import os 
url_filepath="\\".join([os.path.dirname(os.path.abspath(__file__)),"CrawledURLs.txt"])

if os.path.exists(url_filepath):
  os.remove(url_filepath)

file=open(url_filepath,'a+')
  
def crawl_web(initial_url):
    robotURL="/".join([initial_url,"robots.txt"])
    to_crawl =  []
    to_crawl.append(initial_url)
    rp = robotparser.RobotFileParser()
    rp.set_url(robotURL)
    #Reading the robots.txt file
    rp.read() 
    
    #Check if crawl delay is available in robots.txt else set default 0.5 sec (2 requests per second)
    wait_time=rp.crawl_delay("*")
    if wait_time==None: 
        wait_time=0.5
    
    while to_crawl:
        current_url = to_crawl.pop(0)
        time.sleep(wait_time)
        r = requests.get(current_url, timeout=5)
        if r.status_code==200:
            file.write(current_url)
            file.write('\n')
            for url in re.findall('<a href="([^"]+)">', str(r.content)):
                if url[0] == '/':
                    url = current_url + url
                pattern = re.compile('http?')
                if pattern.match(url) and rp.can_fetch("*", url):
                    to_crawl.append(url)
    file.close()                

if __name__=="__main__":
    crawl_web(sys.argv[1])