from __future__ import division, print_function, absolute_import
import tflearn
from tflearn.data_utils import shuffle
from tflearn.layers.core import input_data, dropout, fully_connected
from tflearn.layers.conv import conv_2d, max_pool_2d
from tflearn.layers.estimator import regression
from tflearn.data_preprocessing import ImagePreprocessing
from tflearn.data_augmentation import ImageAugmentation
from keras.datasets import cifar10
import pickle
import pandas as pd


print('Loading Dataset...')
# Load the data set
# X, Y, X_test, Y_test = pickle.load(open("full_dataset.pkl", "rb"))
# X, Y, X_test, Y_test = pickle.load(open("cifar-10-batches-py/data_batch_1", 'rb'))
# X, Y = pickle.load(open("cifar-10-batches-py/data_batch_1", 'rb'))
dic = pickle.load(open("cifar-10-batches-py/data_batch_1", mode='rb'))
X = dic['data'].reshape((len(dic['data']), 3, 32, 32)).transpose(0, 2, 3, 1)

labels = map(lambda cat: 1 if cat == 6 else 0, dic['labels'])
Y = pd.get_dummies(labels).values

# Y = dic['labels']
print('Dataset loaded...')

X, Y = shuffle(X, Y)
print('Dataset shuffled...')

# Make sure the data is normalized
img_prep = ImagePreprocessing()
# img_prep.add_featurewise_zero_center()
# img_prep.add_featurewise_stdnorm()

# Create extra synthetic training data by flipping, rotating and blurring the
# images on our data set.
img_aug = ImageAugmentation()
# img_aug.add_random_flip_leftright()
# img_aug.add_random_rotation(max_angle=25.)
# img_aug.add_random_blur(sigma_max=3.)

# Define our network architecture:
print('Loading Dataset...')

# Input is a 32x32 image with 3 color channels (red, green and blue)
network = input_data(shape=[None, 32, 32, 3], data_preprocessing=img_prep, data_augmentation=img_aug)
# Step 1: Convolution
network = conv_2d(network, 32, 3, activation='relu')

# Step 2: Max pooling
network = max_pool_2d(network, 2)

# Step 3: Convolution again
network = conv_2d(network, 64, 3, activation='relu')

# Step 4: Convolution yet again
network = conv_2d(network, 64, 3, activation='relu')

# Step 5: Max pooling again
network = max_pool_2d(network, 2)

# Step 6: Fully-connected 512 node neural network
network = fully_connected(network, 512, activation='relu')

# Step 7: Dropout - throw away some data randomly during training to prevent over-fitting
network = dropout(network, 0.5)

# Step 8: Fully-connected neural network with two outputs (0=isn't a bird, 1=is a bird) to make the final prediction
network = fully_connected(network, 2, activation='softmax')

# Tell tflearn how we want to train the network
network = regression(network, optimizer='adam', loss='categorical_crossentropy', learning_rate=0.001)

# Wrap the network in a model object
model = tflearn.DNN(network, tensorboard_verbose=0, checkpoint_path='bird-classifier.tfl.ckpt')

# Train it! We'll do 100 training passes and monitor it as it goes.
# model.fit(X, Y, n_epoch=100, shuffle=True, validation_set=(X_test, Y_test),
model.fit(X, Y, n_epoch=100, shuffle=True, show_metric=True, batch_size=96, snapshot_epoch=True, run_id='bird-classifier')

# Save model when training is complete to a file
model.save("bird-classifier.tfl")
print("Network trained and saved as bird-classifier.tfl!")
