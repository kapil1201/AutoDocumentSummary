# -*- coding: utf-8 -*-
"""
Created on Mon Oct  8 15:17:47 2018

@author: Kapil.Gurjar
"""

import mnist_loader
import network
training_data, test_data = mnist_loader.load_data_wrapper()


net = network.Network([784,30, 10])
#SGD(training_data, epochs, mini_batch_size, eta,test_data)
net.SGD(training_data, 30, 10, 3.0, test_data=test_data)
