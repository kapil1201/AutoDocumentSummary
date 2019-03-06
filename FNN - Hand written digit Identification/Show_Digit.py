# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 19:34:55 2018

@author: Kapil.Gurjar
"""
import numpy as np
import scipy.misc as smp
import time
import mnist_loader

training_data, test_data = mnist_loader.load_data_wrapper()
training_data=list(training_data)

#Show random digit
index=np.random.randint(0,len(training_data)-1)
open("C:/Users/kapil.gurjar/Desktop/ANN Session/Digit_Data.txt","w+").write(str(training_data[index]))
img=smp.toimage(np.reshape(training_data[index][0],(28,28)))
time.sleep(2)
img.show()
