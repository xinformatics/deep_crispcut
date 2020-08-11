# -*- coding: utf-8 -*-
"""classify.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/15gRHF_Fjnjf4ymOV9AFpusunzXafzldh
"""

!pwd

!cp "/content/drive/My Drive/crisprdata/crisprdata.zip" "crisprdata.zip"

!cp "/content/drive/My Drive/crisprdata/output.csv" "output.csv"

!cp "/content/drive/My Drive/crisprdata/output2.csv" "output2.csv"

#now extract the working folder -q is for silent unzip
!unzip -q crisprdata.zip
#this extracts the data to the folder "moredata" which has images

# Commented out IPython magic to ensure Python compatibility.
# %tensorflow_version 1.x

import sys
import numpy as np
import pandas as pd
import os
from tqdm import tqdm
from natsort import natsorted

import matplotlib.pyplot as plt

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline

import keras.metrics

from keras.models import Sequential, Model
from keras.layers import Input, Dense, Dropout, Activation, Concatenate, Flatten, MaxPooling2D, Convolution2D, Convolution1D, MaxPooling1D, GlobalMaxPooling1D, BatchNormalization, LSTM, GRU, Bidirectional
from keras.regularizers import l2,l1
from keras.optimizers import SGD,Adam,RMSprop
from tensorflow.compat.v1 import InteractiveSession
import keras.backend as K
from keras.preprocessing.image import array_to_img, img_to_array, load_img
from keras.callbacks import EarlyStopping, ModelCheckpoint,ReduceLROnPlateau
from keras.models import load_model

from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()

import tensorflow as tf
print(tf.__version__)

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

from keras.utils import to_categorical, plot_model

off    = natsorted(os.listdir('moredata/off/'))
target = natsorted(os.listdir('moredata/target/'))

#checking if data loaded correctly or not
off[:10],target[:10]

#len(off),len(target)
samples = len(off)

samples

# height x width is the standard
dims = (4,28)
#ideal 4x28
#actual 54x390
shape = (samples, dims[0], dims[1], 1)     

off_dataset = np.ndarray(shape=shape,dtype=np.float32)
target_dataset = np.ndarray(shape=shape,dtype=np.float32)

off_dataset.shape, target_dataset.shape

#del off_dataset,target_dataset

#load off-target images
i=0
for item in off:
    img1 = load_img('moredata/off/'+ item, target_size=dims, color_mode='grayscale',interpolation='nearest')  # this is a PIL image
    # Convert to Numpy Array
    x1 = img_to_array(img1)
    off_dataset[i] = x1
    i += 1
    if i % 20000 == 0:
        print("%d images to array" % i)

print("All off target images done!")

j=0
for item in target:
    img2 = load_img('moredata/target/'+ item, target_size=dims, color_mode='grayscale',interpolation='nearest')  # this is a PIL image
    # Convert to Numpy Array
    x2 = img_to_array(img2)
    target_dataset[j] = x2
    j += 1
    if j % 20000 == 0:
        print("%d images to array" % j)

print("All target images done!")

#above part is common to all models

#########################
# CLASSIFICATION MODULE #
########################

# now load the output values
#output = pd.read_csv('output.csv')
output = pd.read_csv('output2.csv')

#get class output
y = output['y']
y

from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()

Y = le.fit_transform(y).reshape(-1,1)

#get regression output

#data summary
off_dataset.shape, target_dataset.shape, Y.shape

# #from sklearn.utils import class_weight
# class_weights = class_weight.compute_class_weight('balanced',np.unique(Y_train.squeeze()),Y_train.squeeze())
# class_weights[0] , class_weights[1]
# w_dict = {0: 0.524, 1: 10.677}

classes = Y.squeeze()

classes

off, target = np.bincount(classes)
total_count = len(classes)
weight_off = (1 / off) * (total_count) / 2.0
weight_target = (1 / target) * (total_count) / 2.0
c_weights = {0: round(weight_off,3), 1: round(weight_target,3)}
c_weights

#now model
try:
  del model, history
except:
  pass

from keras import backend as K
K.clear_session()

#model start
#####################################################

#input_1

input_1 = Input(shape = (4,28))
conv1_1 = Convolution1D(1024, 3, activation = 'relu',padding='same')(input_1)
pool1_1 = MaxPooling1D(pool_size=2)(conv1_1)
conv1_2 = Convolution1D(1024, 3, activation = 'relu',padding='same')(pool1_1)
pool1_2 = MaxPooling1D(pool_size=2)(conv1_2)
flat_1 = Flatten()(pool1_2)
 
#input_2

input_2 = Input(shape = (4,28))
conv2_1 = Convolution1D(1024, 3, activation = 'relu',padding='same')(input_2)
pool2_1 = MaxPooling1D(pool_size=2)(conv2_1)
conv2_2 = Convolution1D(1024, 3, activation = 'relu',padding='same')(pool2_1)
pool2_2 = MaxPooling1D(pool_size=2)(conv2_2)
flat_2 = Flatten()(pool2_2)
 
# concatenate
concat   = Concatenate()([flat_1, flat_2])
dense1   = Dense(4096, activation = 'relu')(concat)
#dropout1 = Dropout(0.1)(dense1)
dense2   = Dense(2048, activation = 'relu')(dense1)
dense3   = Dense(1024, activation = 'relu')(dense2)
output   = Dense(1, activation = 'sigmoid')(dense3)
 
# create model with two inputs
model = Model(inputs=[input_1,input_2], outputs=[output])

model.summary()

#plot_model(model,  to_file='model.png', show_shapes=True, show_layer_names=True)

metrics = [
    keras.metrics.FalseNegatives(name="fn"),
    keras.metrics.FalsePositives(name="fp"),
    keras.metrics.TrueNegatives(name="tn"),
    keras.metrics.TruePositives(name="tp"),
    keras.metrics.BinaryAccuracy(name='accuracy'),
    keras.metrics.Precision(name="precision"),
    keras.metrics.Recall(name="recall"),
    keras.metrics.AUC(name="auc")
]

#model compile
model.compile(optimizer=keras.optimizers.Adam(lr=0.0001),loss='binary_crossentropy',metrics=metrics)

# # data split for 1D- not used, squeeze is used for removing the channel dimension
off_dataset1d = off_dataset.squeeze()
target_dataset1d = target_dataset.squeeze()
off_dataset_train, off_dataset_test, target_dataset_train, target_dataset_test, Y_train, Y_test = train_test_split(off_dataset1d, target_dataset1d,Y, test_size=0.1, random_state=1)

early_stopping = EarlyStopping(monitor='val_loss', patience=30,restore_best_weights=True, verbose=1)

reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.1,patience=5, min_lr=0.000001, verbose=1)

history=model.fit([off_dataset_train,target_dataset_train], Y_train, 
                batch_size=16, 
                epochs=50, 
                verbose=1, 
                validation_split=0.1,
                #callbacks=[reduce_lr],
                class_weight=c_weights
                )

#training plots
fig = plt.figure(figsize=(15,20))
plt.subplot(3,2,1)
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title("Classification losses")
plt.ylabel("Classification Losses")
plt.xlabel("Epoch")
plt.legend(["Training Classification Loss","Valid Classification Loss"])
plt.subplot(3,2,2)
plt.plot(history.history['fn'])
plt.plot(history.history['val_fn'])
plt.plot(history.history['fp'])
plt.plot(history.history['val_fp'])
plt.plot(history.history['tn'])
plt.plot(history.history['val_tn'])
plt.plot(history.history['tp'])
plt.plot(history.history['val_tp'])
plt.title("Confusion Values")
plt.ylabel("Confusion Values")
plt.xlabel("Epoch")
plt.legend(["Training FN","Valid FN","Training FP","Valid FP","Training TN","Valid TN","Training TP","Valid TP"])
plt.subplot(3,2,3)
plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title("Classification Accuracy")
plt.ylabel("Classification Accuracy")
plt.xlabel("Epoch")
plt.legend(["Training Classification Accuracy","Valid Classification Accuracy"])
plt.subplot(3,2,4)
plt.plot(history.history['precision'])
plt.plot(history.history['val_precision'])
plt.title("Classification precision")
plt.ylabel("Classification precision")
plt.xlabel("Epoch")
plt.legend(["Training Classification precision","Valid Classification precision"])
plt.subplot(3,2,5)
plt.plot(history.history['recall'])
plt.plot(history.history['val_recall'])
plt.title("Classification recall")
plt.ylabel("Classification recall")
plt.xlabel("Epoch")
plt.legend(["Training Classification recall","Valid Classification recall"])
plt.subplot(3,2,6)
plt.plot(history.history['auc'])
plt.plot(history.history['val_auc'])
plt.title("Classification auc")
plt.ylabel("Classification auc")
plt.xlabel("Epoch")
plt.legend(["Training Classification auc","Valid Classification auc"])
plt.show()

Y_test.shape

# predict on test set
y_test_pred = model.predict([off_dataset_test,target_dataset_test])

y_test_pred.shape

from sklearn.metrics import precision_recall_curve
from sklearn.metrics import average_precision_score
from sklearn.metrics import roc_curve, auc

fpr = dict()
tpr = dict()
roc_auc = dict()

for i in range(1):
    fpr[i], tpr[i], _ = roc_curve(Y_test[:, i], y_test_pred[:, i])
    roc_auc[i] = auc(fpr[i], tpr[i])

# Plot of a ROC curve for a specific class
fig, ax = plt.subplots(figsize=(8,7))
ax.plot(fpr[0], tpr[0],label=' (AUC: %0.2f)' % roc_auc[0], alpha=1)
ax.plot([0, 1], [0, 1], 'k--')
ax.set_ylim([0.0, 1.01])
ax.set_xlim([0.0, 1.01])
ax.set_yticks(np.arange(0, 1.1, 0.1))
ax.set_xticks(np.arange(0, 1.1, 0.1))
ax.set_xlabel('False Positive Rate', fontsize=14)
ax.set_ylabel('True Positive Rate', fontsize=14)
ax.tick_params(axis="x", labelsize=12)
ax.tick_params(axis="y", labelsize=12) 
ax.grid()
ax.legend(fontsize=12)
plt.savefig('roc.png', dpi=500, bbox_inches='tight')

precision = dict()
recall = dict()
average_precision = dict()
for i in range(1):
    precision[i], recall[i], _ = precision_recall_curve(Y_test[:, i], y_test_pred[:, i])
    average_precision[i] = average_precision_score(Y_test[:, i], y_test_pred[:, i])

# A "micro-average": quantifying score on all classes jointly
precision["micro"], recall["micro"], _ = precision_recall_curve(Y_test.ravel(), y_test_pred.ravel())
average_precision["micro"] = average_precision_score(Y_test, y_test_pred, average="micro")
#print('Average precision score , micro-averaged over all classes: {0:0.2f}'
#    .format(average_precision["micro"]))

fig, ax = plt.subplots(figsize=(8,7))
ax.step(recall['micro'], precision['micro'], where='post')

ax.set_xlabel('Recall', fontsize=14)
ax.set_ylabel('Precision', fontsize=14)
ax.plot([0, 1], [1, 0], 'k--')
ax.set_ylim([0.0, 1.01])
ax.set_xlim([0.0, 1.00])
ax.set_yticks(np.arange(0, 1.1, 0.1))
ax.set_xticks(np.arange(0, 1.1, 0.1))
ax.set_title('AP={0:0.2f}'.format(average_precision["micro"]), fontsize=14)
ax.tick_params(axis="x", labelsize=12)
ax.tick_params(axis="y", labelsize=12) 
ax.grid(linestyle='-.', linewidth=0.7)
plt.savefig('aupr.png', dpi=500, bbox_inches='tight')

#confusion matrix
from sklearn.metrics import plot_confusion_matrix
from sklearn import metrics

y_label_pred = np.where(y_test_pred > 0.5, 1, 0)

y_label_pred,y_label_pred.shape

print(metrics.confusion_matrix(Y_test, y_label_pred))

print(metrics.classification_report(Y_test, y_label_pred, digits=3))

# now testing regression
#########################
#      REGRESSION #######
########################

freq = output['freq']

freq,freq.shape

freq = freq.values.reshape(-1,1)
freq

#data summary
off_dataset.shape, target_dataset.shape, freq.shape

# # data split for 1D- not used, squeeze is used for removing the channel dimension
off_dataset1d = off_dataset.squeeze()
target_dataset1d = target_dataset.squeeze()
off_dataset_train, off_dataset_test, target_dataset_train, target_dataset_test, freq_train, freq_test = train_test_split(off_dataset1d, target_dataset1d,freq, test_size=0.1, random_state=1)

#now model
try:
  del model, history
except:
  pass

from keras import backend as K
K.clear_session()

#model start
#####################################################

#input_1

input_1 = Input(shape = (4,28))
conv1_1 = Convolution1D(1024, 3, activation = 'relu',padding='same')(input_1)
pool1_1 = MaxPooling1D(pool_size=2)(conv1_1)
conv1_2 = Convolution1D(2048, 3, activation = 'relu',padding='same')(pool1_1)
pool1_2 = MaxPooling1D(pool_size=2)(conv1_2)
flat_1 = Flatten()(pool1_2)
 
#input_2

input_2 = Input(shape = (4,28))
conv2_1 = Convolution1D(1024, 3, activation = 'relu',padding='same')(input_2)
pool2_1 = MaxPooling1D(pool_size=2)(conv2_1)
conv2_2 = Convolution1D(2048, 3, activation = 'relu',padding='same')(pool2_1)
pool2_2 = MaxPooling1D(pool_size=2)(conv2_2)
flat_2 = Flatten()(pool2_2)
 
# concatenate
concat   = Concatenate()([flat_1, flat_2])
dense1   = Dense(2048, activation = 'relu')(concat)
#dropout1 = Dropout(0.1)(dense1)
dense2   = Dense(2048, activation = 'relu')(dense1)
dense3   = Dense(1024, activation = 'relu')(dense2)
output   = Dense(1, activation = 'linear')(dense3)
 
# create model with two inputs
model = Model(inputs=[input_1,input_2], outputs=[output])

#model compile
model.compile(optimizer=keras.optimizers.Adam(lr=0.00001),loss='mse',metrics=['mse'])
#model.compile(optimizer=RMSprop(),loss='mse',metrics=['mse'])

reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.1,patience=5, min_lr=0.00001, verbose=1)

early_stopping = EarlyStopping(monitor='val_loss', patience=20,restore_best_weights=True, verbose=1)

history=model.fit([off_dataset_train,target_dataset_train], freq_train, 
                batch_size=32, 
                epochs=100, 
                verbose=1, 
                validation_split=0.1,
                callbacks=[reduce_lr]
                )

fig = plt.figure(figsize=(5,5))
plt.plot(history.history['loss'][1:])
plt.plot(history.history['val_loss'])
plt.title("Regression losses")
plt.ylabel("Regression Losses")
plt.xlabel("Epoch")
plt.legend(["Training Regression Loss","Valid Regression Loss"])
plt.show()

#model predictions
ypred_train = model.predict([off_dataset_train, target_dataset_train])
ypred_test = model.predict([off_dataset_test, target_dataset_test])

#freq_train.shape, ypred_train.shape,  freq_test.shape, ypred_test.shape

from sklearn.metrics import r2_score

print('training_r2', r2_score(freq_train, ypred_train))
print('test_r2', r2_score(freq_test, ypred_test))



fig, ax = plt.subplots()
ax.scatter(freq_train, ypred_train,s=5)
ax.plot([freq.min(), freq.max()], [freq.min(), freq.max()], 'k--', lw=1)
ax.set_xlabel('Actual')
ax.set_ylabel('Predicted')
ax.set_title('Traing Set R2: ' + str(r2_score(freq_train, ypred_train)),)
plt.show()

fig, ax = plt.subplots()
ax.scatter(freq_test, ypred_test,s=5)
ax.plot([freq.min(), freq.max()], [freq.min(), freq.max()], 'k--', lw=1)
ax.set_xlabel('Actual')
ax.set_ylabel('Predicted')
ax.set_title('Test Set R2: ' + str(r2_score(freq_test, ypred_test)))
plt.show()

###################
#multitask learning; classification regression from shared layers
###################

#get both types of output
output = pd.read_csv('output2.csv')
y = output['y']
freq = output['freq']

Y = le.fit_transform(y).reshape(-1,1)

Y, Y.shape

freq = freq.values.reshape(-1,1)
freq, freq.shape

#data summary
off_dataset.shape, target_dataset.shape, Y.shape, freq.shape

#now model
try:
  del model, history
except:
  pass

from keras import backend as K
K.clear_session()

#model
#model start
#####################################################

#input_1

input_1 = Input(shape = (4,28), name='i_1')
conv1_1 = Convolution1D(1024, 3, activation = 'relu',padding='same')(input_1)
pool1_1 = MaxPooling1D(pool_size=2)(conv1_1)
conv1_2 = Convolution1D(1024, 3, activation = 'relu',padding='same')(pool1_1)
pool1_2 = MaxPooling1D(pool_size=2)(conv1_2)
flat_1 = Flatten()(pool1_2)
 
#input_2

input_2 = Input(shape = (4,28), name='i_2')
conv2_1 = Convolution1D(1024, 3, activation = 'relu',padding='same')(input_2)
pool2_1 = MaxPooling1D(pool_size=2)(conv2_1)
conv2_2 = Convolution1D(1024, 3, activation = 'relu',padding='same')(pool2_1)
pool2_2 = MaxPooling1D(pool_size=2)(conv2_2)
flat_2 = Flatten()(pool2_2)
 
# concatenate
concat   = Concatenate()([flat_1, flat_2])
dense1   = Dense(2048, activation = 'relu')(concat)
#dropout1 = Dropout(0.1)(dense1)
#dense2   = Dense(1024, activation = 'relu')(dense1)
dense3   = Dense(512, activation = 'relu')(dense1) #goes to regression


#dense4  = Dense(1024, activation = 'relu')(dense1)
dense5  = Dense(1024, activation = 'relu')(dense1) #goes to classification


#regression output
output_1  = Dense(1, activation = 'linear', name='r')(dense3)


#classification output
output_2  = Dense(1, activation = 'sigmoid', name='c')(dense5)
 
# create model with two inputs
model = Model(inputs=[input_1,input_2], outputs=[output_1,output_2])

model.summary()

plot_model(model,  to_file='model_multi5_latest.png', show_shapes=True, show_layer_names=True)

#metrics for classification
metrics = [
    #keras.metrics.FalseNegatives(name="fn"),
    #keras.metrics.FalsePositives(name="fp"),
    #keras.metrics.TrueNegatives(name="tn"),
    #keras.metrics.TruePositives(name="tp"),
    #keras.metrics.BinaryAccuracy(name='accuracy'),
    keras.metrics.Precision(name="precision"),
    keras.metrics.Recall(name="recall"),
    keras.metrics.AUC(name="auc")
]

#model compile is one of the most important step
model.compile(optimizer=keras.optimizers.Adam(lr=0.0001),
              loss={'r': 'mse','c': 'binary_crossentropy'},
              loss_weights={'r': 0.0001,'c': 1.0},
              metrics={'r':'mse','c':metrics})

# # data split for 1D- not used, squeeze is used for removing the channel dimension
# use of indexes to refer data later
img_indexes = list(range(0,samples))
off_dataset1d = off_dataset.squeeze()
target_dataset1d = target_dataset.squeeze()
off_dataset_train, off_dataset_test, target_dataset_train, target_dataset_test, Y_train, Y_test, freq_train, freq_test, train_index, test_index = train_test_split(off_dataset1d, target_dataset1d,Y,freq,img_indexes, test_size=0.1, random_state=1)

#train summary
off_dataset_train.shape,target_dataset_train.shape,freq_train.shape,Y_train.shape

#test summary
off_dataset_test.shape, target_dataset_test.shape, freq_test.shape,Y_test.shape

early_stopping = EarlyStopping(monitor='val_loss', patience=30,restore_best_weights=True, verbose=1)

reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5,patience=5, min_lr=0.00000001, verbose=1)

# history=model.fit({'i_1': off_dataset_train,'i_2' : target_dataset_train},
#                   {'r':freq_train,'c': Y_train}, 
#                 batch_size=16, epochs=50,
#                 validation_split=0.1)
#                 #validation_data=({'i_1':off_dataset_test,'i_2':target_dataset_test},{'r': freq_test,'c': Y_test}),
#                 #verbose=1)

try:
  history=model.fit([off_dataset_train,target_dataset_train],[freq_train,Y_train], 
                  batch_size=16, epochs=30, 
                  #validation_data=([off_dataset_test,target_dataset_test],[freq_test,Y_test]),
                  #class_weight={0: 0.525, 1: 10.704},
                  validation_split=0.1,
                  class_weight={'c': {0: 0.525, 1: 10.704}},
                  callbacks=[reduce_lr],verbose=1)
except KeyboardInterrupt:
  model.save('model_multi5_latest.hdf5')
  print('Model saved to drive')

model.save('model_multi5_latest.hdf5')

#training plots
fig = plt.figure(figsize=(15,20))
plt.subplot(3,2,1)
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title("Total losses")
plt.ylabel("Total Losses")
plt.xlabel("Epoch")
plt.legend(["Training Total Loss","Valid Total Loss"])
plt.subplot(3,2,2)
plt.plot(history.history['r_loss'])
plt.plot(history.history['val_r_loss'])
plt.title("Regression Loss")
plt.ylabel("Regression Loss")
plt.xlabel("Epoch")
plt.legend(["Training Regression Loss","Validation Regression Loss"])
plt.subplot(3,2,3)
plt.plot(history.history['r_mse'])
plt.plot(history.history['val_r_mse'])
plt.title("Regression MSE")
plt.ylabel("Regression MSE")
plt.xlabel("Epoch")
plt.legend(["Training Regression MSE","Valid Regression MSE"])
plt.subplot(3,2,4)
plt.plot(history.history['c_precision'])
plt.plot(history.history['val_c_precision'])
plt.title("Classification precision")
plt.ylabel("Classification precision")
plt.xlabel("Epoch")
plt.legend(["Training Classification precision","Valid Classification precision"])
plt.subplot(3,2,5)
plt.plot(history.history['c_recall'])
plt.plot(history.history['val_c_recall'])
plt.title("Classification recall")
plt.ylabel("Classification recall")
plt.xlabel("Epoch")
plt.legend(["Training Classification recall","Valid Classification recall"])
plt.subplot(3,2,6)
plt.plot(history.history['c_auc'])
plt.plot(history.history['val_c_auc'])
plt.title("Classification auc")
plt.ylabel("Classification auc")
plt.xlabel("Epoch")
plt.legend(["Training Classification auc","Valid Classification auc"])
plt.show()

# predict on test set
yreg_pred, ycls_pred = model.predict([off_dataset_test,target_dataset_test])

# predict on training set for regression comparison of r2
yreg_pred_train, _ = model.predict([off_dataset_train,target_dataset_train])

yreg_pred.shape, ycls_pred.shape

#plots
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import average_precision_score
from sklearn.metrics import roc_curve, auc

fpr = dict()
tpr = dict()
roc_auc = dict()

for i in range(1):
    fpr[i], tpr[i], _ = roc_curve(Y_test[:, i], ycls_pred[:, i])
    roc_auc[i] = auc(fpr[i], tpr[i])

# Plot of a ROC curve for a specific class
fig, ax = plt.subplots(figsize=(8,7))
ax.plot(fpr[0], tpr[0],label=' (AUC: %0.2f)' % roc_auc[0], alpha=1)
ax.plot([0, 1], [0, 1], 'k--')
ax.set_ylim([0.0, 1.01])
ax.set_xlim([0.0, 1.01])
ax.set_yticks(np.arange(0, 1.1, 0.1))
ax.set_xticks(np.arange(0, 1.1, 0.1))
ax.set_xlabel('False Positive Rate', fontsize=14)
ax.set_ylabel('True Positive Rate', fontsize=14)
ax.tick_params(axis="x", labelsize=12)
ax.tick_params(axis="y", labelsize=12) 
ax.grid()
ax.legend(fontsize=12)
plt.savefig('roc.png', dpi=500, bbox_inches='tight')

precision = dict()
recall = dict()
average_precision = dict()
for i in range(1):
    precision[i], recall[i], _ = precision_recall_curve(Y_test[:, i], ycls_pred[:, i])
    average_precision[i] = average_precision_score(Y_test[:, i], ycls_pred[:, i])

# A "micro-average": quantifying score on all classes jointly
precision["micro"], recall["micro"], _ = precision_recall_curve(Y_test.ravel(), ycls_pred.ravel())
average_precision["micro"] = average_precision_score(Y_test, ycls_pred, average="micro")
#print('Average precision score , micro-averaged over all classes: {0:0.2f}'
#    .format(average_precision["micro"]))

fig, ax = plt.subplots(figsize=(8,7))
ax.step(recall['micro'], precision['micro'], where='post')

ax.set_xlabel('Recall', fontsize=14)
ax.set_ylabel('Precision', fontsize=14)
ax.plot([0, 1], [1, 0], 'k--')
ax.set_ylim([0.0, 1.01])
ax.set_xlim([0.0, 1.00])
ax.set_yticks(np.arange(0, 1.1, 0.1))
ax.set_xticks(np.arange(0, 1.1, 0.1))
ax.set_title('AP={0:0.2f}'.format(average_precision["micro"]), fontsize=14)
ax.tick_params(axis="x", labelsize=12)
ax.tick_params(axis="y", labelsize=12) 
ax.grid(linestyle='-.', linewidth=0.7)
plt.savefig('aupr.png', dpi=500, bbox_inches='tight')

#confusion matrix
from sklearn.metrics import plot_confusion_matrix
from sklearn import metrics as sklearn_metrics

y_label_pred = np.where(ycls_pred > 0.5, 1, 0)

y_label_pred,y_label_pred.shape

print(sklearn_metrics.confusion_matrix(Y_test, y_label_pred))

print(sklearn_metrics.classification_report(Y_test, y_label_pred, digits=3))

#now regression
freq_train.shape, yreg_pred_train.shape

freq_test.shape, yreg_pred.shape

from sklearn.metrics import r2_score

print('training_r2', r2_score(freq_train, yreg_pred_train))
print('test_r2', r2_score(freq_test, yreg_pred))

fig, ax = plt.subplots()
ax.scatter(freq_train, yreg_pred_train,s=5)
ax.plot([freq.min(), freq.max()], [freq.min(), freq.max()], 'k--', lw=1)
ax.set_xlabel('Actual')
ax.set_ylabel('Predicted')
ax.set_title('Traing Set R2: ' + str(r2_score(freq_train, yreg_pred_train)),)
plt.show()

fig, ax = plt.subplots()
ax.scatter(freq_test, yreg_pred,s=5)
ax.plot([freq.min(), freq.max()], [freq.min(), freq.max()], 'k--', lw=1)
ax.set_xlabel('Actual')
ax.set_ylabel('Predicted')
ax.set_title('Test Set R2: ' + str(r2_score(freq_test, yreg_pred)))
plt.show()

# # weighted binary crossentropy
# def get_weighted_loss(weights):
#     def weighted_loss(y_true, y_pred):
#         return K.mean((weights[:,0]**(1-y_true))*(weights[:,1]**(y_true))*K.binary_crossentropy(y_true, y_pred), axis=-1)
#     return weighted_loss

# model.compile(optimizer=Adam(), loss=get_weighted_loss(class_weights))

