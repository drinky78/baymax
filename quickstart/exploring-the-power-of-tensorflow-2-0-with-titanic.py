#!/usr/bin/env python
# coding: utf-8

# # Description
# The purpose of this kernel is to explore the new TensorFlow 2.0 API to achieve the ML results fast and easily with efficiency optimizations built-in.
# ### Trying to automate the feature engineering and ensemble process. Both CPU and GPU compatible
# ### This kernel is by no means comprehensive and accurate but serve as a starting point. 
# ### I hope it will make some people's life easier in getting started with new TensorFlow version.
# I will not be focussing on the utility provided by TensorFlow to convert old tf code to 2.0
# ### Will try to see if we can get away without extensively preprocessing the data and get tensorflow to handle the data types

# In[1]:


# Utilities
import datetime
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings("ignore")
import os

# Numericals
import numpy as np
import pandas as pd

# Plotting
import seaborn as sns
import matplotlib.pyplot as plt
sns.set_style("darkgrid")
#get_ipython().run_line_magic('matplotlib', 'inline')

# TensorFlo 2.0
#get_ipython().system('pip install -q tensorflow==2.0.0-alpha0')
import tensorflow as tf
# Load the TensorBoard notebook extension
#get_ipython().run_line_magic('load_ext', 'tensorboard.notebook')
# Imports for the HParams plugin from tensorboard
from tensorboard.plugins.hparams import api_pb2
from tensorboard.plugins.hparams import summary as hparams_summary
from google.protobuf import struct_pb2

from tflearn.datasets import titanic

# Clear any logs from previous runs
#get_ipython().system('rm -rf ./logs/ ')


# In[2]:


filename = 'var/titanic_dataset.csv'
titanic.download_dataset(filename)

dataset = pd.read_csv(filename)

train_data, test_data = train_test_split(dataset, test_size=0.2)

train_data.info()
print('_'*50)
test_data.info()


# In[3]:


train_data.head()


# In[4]:


train_data.describe()


# ### Drop the columns if the missing values are more than 20% of the data. Drop missing rows otherwise

# In[5]:


for col in train_data.columns:
    if len(train_data[col].dropna()) <= (0.7 * len(train_data)):
        train_data.drop(columns=[col], inplace=True)
    else:
        train_data.dropna(axis=0, subset=[col],inplace=True)

for col in test_data.columns:
    if len(test_data[col].dropna()) <= (0.7 * len(test_data)):
        test_data.drop(columns=[col], inplace=True)
    else:
        test_data[col].fillna(value=test_data[col].mode()[0] ,inplace=True)


# In[6]:


train_data.info()
print('_'*50)
test_data.info()


# ## No need to convert the data types from categorical to numerical because we want tensorflow to handle this kind of data

# ## Define Feature columns for tensorflow
# Examples of each column type

# In[7]:


# Just to see the correlation
plt.figure(figsize=(10,8))
sns.heatmap(train_data.corr(method='pearson'),annot=True,cmap='YlGnBu',fmt='.2f',linewidths=2)


# In[8]:


feature_columns = []

# numeric cols
for header in ['Age', 'Fare']:
  feature_columns.append(tf.feature_column.numeric_column(header))

# bucketized cols
age = tf.feature_column.numeric_column("Age")
age_buckets = tf.feature_column.bucketized_column(age, boundaries=[5, 10, 20, 30, 40, 50, 60, 70, 80])
feature_columns.append(age_buckets)

# indicator cols
categorical_cols = ["Sex", "Embarked", "Pclass", "SibSp", "Parch"]
for col in categorical_cols:
    train_data[col] = train_data[col].apply(str)
    test_data[col] = test_data[col].apply(str)
    cat_column_with_vocab = tf.feature_column.categorical_column_with_vocabulary_list(
          col, list(train_data[col].value_counts().index.values))
    one_hot = tf.feature_column.indicator_column(cat_column_with_vocab)
    feature_columns.append(one_hot)


# embedding cols
ticket = tf.feature_column.categorical_column_with_hash_bucket("Ticket", hash_bucket_size=1000)
ticket_embedding = tf.feature_column.embedding_column(ticket, dimension=8)
feature_columns.append(ticket_embedding)

# crossed cols
p_class = tf.feature_column.categorical_column_with_vocabulary_list(
          "Pclass", list(train_data["Pclass"].value_counts().index.values))
parch = tf.feature_column.categorical_column_with_vocabulary_list(
          "Parch", list(train_data["Parch"].value_counts().index.values))
pclass_parch_crossed = tf.feature_column.crossed_column([p_class, parch], hash_bucket_size=1000)
pclass_parch_crossed = tf.feature_column.indicator_column(pclass_parch_crossed)
feature_columns.append(pclass_parch_crossed)


# In[9]:


# A utility method to create a tf.data dataset from a Pandas Dataframe
def df_to_dataset(dataframe, testing=False, batch_size=32):
    dataframe = dataframe.copy()
    if not testing:
        labels = dataframe.pop('Survived')
        ds = tf.data.Dataset.from_tensor_slices((dict(dataframe), labels))
        ds = ds.shuffle(buffer_size=len(dataframe))
    else:
        ds = tf.data.Dataset.from_tensor_slices(dict(dataframe))
    ds = ds.batch(batch_size)
    ds = ds.prefetch(buffer_size=tf.data.experimental.AUTOTUNE)
    return ds


# In[10]:


train_data, val_data = train_test_split(train_data, test_size=0.2)


# In[11]:


batch_size = 32
train_ds = df_to_dataset(train_data, batch_size=batch_size)
val_ds = df_to_dataset(val_data, batch_size=batch_size)
test_ds = df_to_dataset(test_data, testing=True, batch_size=batch_size)


# # Setup Hyperparameter tuning

# In[12]:


num_units_list = [128, 256]
dropout_rate_list = [0.2, 0.5] 
optimizer_list = ['adam', 'sgd'] 


# In[13]:


# Utility method to create summary for tensorboard
def create_experiment_summary(num_units_list, dropout_rate_list, optimizer_list):
  num_units_list_val = struct_pb2.ListValue()
  num_units_list_val.extend(num_units_list)
  dropout_rate_list_val = struct_pb2.ListValue()
  dropout_rate_list_val.extend(dropout_rate_list)
  optimizer_list_val = struct_pb2.ListValue()
  optimizer_list_val.extend(optimizer_list)
  return hparams_summary.experiment_pb(
      # The hyperparameters being changed
      hparam_infos=[
          api_pb2.HParamInfo(name='num_units',
                             display_name='Number of units',
                             type=api_pb2.DATA_TYPE_FLOAT64,
                             domain_discrete=num_units_list_val),
          api_pb2.HParamInfo(name='dropout_rate',
                             display_name='Dropout rate',
                             type=api_pb2.DATA_TYPE_FLOAT64,
                             domain_discrete=dropout_rate_list_val),
          api_pb2.HParamInfo(name='optimizer',
                             display_name='Optimizer',
                             type=api_pb2.DATA_TYPE_STRING,
                             domain_discrete=optimizer_list_val)
      ],
      # The metrics being tracked
      metric_infos=[
          api_pb2.MetricInfo(
              name=api_pb2.MetricName(
                  tag='accuracy'),
              display_name='Accuracy'),
      ]
  )

exp_summary = create_experiment_summary(num_units_list, dropout_rate_list, optimizer_list)
root_logdir_writer = tf.summary.create_file_writer("logs/hparam_tuning")
with root_logdir_writer.as_default():
  tf.summary.import_event(tf.compat.v1.Event(summary=exp_summary).SerializeToString())


# In[14]:


# Model compiler
def train_test_model(hparams):

  model = tf.keras.models.Sequential([
    tf.keras.layers.DenseFeatures(feature_columns),
    tf.keras.layers.Dense(hparams['num_units'], activation='relu'),
    tf.keras.layers.Dropout(hparams['dropout_rate']),
      tf.keras.layers.Dense(hparams['num_units'], activation='relu'),
    tf.keras.layers.Dense(2, activation='sigmoid')
  ])
  model.compile(optimizer=hparams['optimizer'],
                loss='binary_crossentropy',
                metrics=['accuracy'])

  model.fit(train_ds, 
            validation_data=val_ds, 
            epochs=50,
            use_multiprocessing=True,
            verbose=0)
  _, accuracy = model.evaluate(val_ds)
  return model, accuracy


# In[15]:


# Model runner
def run(run_dir, hparams):
  writer = tf.summary.create_file_writer(run_dir)
  summary_start = hparams_summary.session_start_pb(hparams=hparams)

  with writer.as_default():
    model, accuracy = train_test_model(hparams)
    summary_end = hparams_summary.session_end_pb(api_pb2.STATUS_SUCCESS)
      
    tf.summary.scalar('accuracy', accuracy, step=1, description="The accuracy")
    tf.summary.import_event(tf.compat.v1.Event(summary=summary_start).SerializeToString())
    tf.summary.import_event(tf.compat.v1.Event(summary=summary_end).SerializeToString())
  return model, accuracy


# In[16]:


model_dict = {}
session_num = 0
for num_units in num_units_list:
    for dropout_rate in dropout_rate_list:
        for optimizer in optimizer_list:
            hparams = {'num_units': num_units, 'dropout_rate': dropout_rate, 'optimizer': optimizer}
            print('--- Running training session %d' % (session_num + 1))
            print(hparams)
            run_name = "run-%d" % session_num
            model, accuracy = run("logs/hparam_tuning/" + run_name, hparams)
            print(accuracy)
            model_dict[accuracy] = model
            session_num += 1


# In[17]:


best_model = model_dict[max(list(model_dict.keys()))]


# In[18]:


predictions = best_model.predict(test_ds)
predictions = np.argmax(predictions, axis=1)


# In[19]:


predictions_dataframe = test_data[["PassengerId"]]
predictions_dataframe["Survived"] = predictions


# In[20]:


predictions_dataframe.to_csv("gender_submission.csv",index=False)


# In[21]:


best_model.save('best_model.h5')


# # It is this easy to save the model in tensorflow now. Reload is the same - with weights :)

# In[22]:




