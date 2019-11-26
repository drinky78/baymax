from __future__ import print_function
import numpy as np
import tflearn
import pandas as pd
from tflearn.datasets import titanic
from tflearn.data_utils import load_csv
import tensorflow as tf;

print(tf.__version__)

filename = 'var/titanic_dataset.csv'
titanic.download_dataset(filename)

dataset = pd.read_csv(filename)
labels = pd.get_dummies(dataset['survived']).values
dataset = dataset.drop(columns='name').drop(columns='ticket').drop(columns='survived')
dataset['sex'] = dataset['sex'].apply(lambda sex: 1 if sex == 'female' else 0)

data = dataset.values

# Build neural network
net = tflearn.input_data(shape=[None, 6])
net = tflearn.fully_connected(net, 32)
net = tflearn.fully_connected(net, 32)
net = tflearn.fully_connected(net, 2, activation='softmax')
net = tflearn.regression(net)
model = tflearn.DNN(net)

# Start training (apply gradient descent algorithm)
model.fit(data, labels, n_epoch=20, batch_size=16, show_metric=True, run_id='titanic')

# Let's create some data for DiCaprio and Winslet
dicaprio = [3, 0, 19, 0, 0, 5.0000]
winslet = [1, 1, 17, 1, 2, 100.0000]
# Predict surviving chances (class 1 results)
pred = model.predict([dicaprio, winslet])
print("DiCaprio Surviving Rate:", pred[0][1])
print("Winslet Surviving Rate:", pred[1][1])
