#FROM tensorflow/tensorflow:latest-gpu-jupyter
FROM tensorflow/tensorflow:nightly-py3-jupyter

RUN apt update
RUN apt install python3-pip

#RUN apt install pip3 -y
RUN pip3 install pip --upgrade

RUN cd /usr/bin && unlink python && ln -s /usr/bin/python3.5 python

# RUN python3
RUN python -m pip install --user numpy scipy matplotlib pandas sklearn pandas_datareader
RUN python -m pip install --user keras tflearn gym flake8
RUN python -m pip install --user tensorflow_hub && tensorflow_text>=2.0.0rc0

WORKDIR /app





