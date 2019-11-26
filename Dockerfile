#FROM tensorflow/tensorflow:latest-gpu-jupyter
FROM tensorflow/tensorflow:nightly-py3-jupyter

# RUN python3
# RUN python3 -m pip install --user numpy scipy matplotlib pandas sklearn pandas_datareader

#RUN apt install pip3 -y
#RUN pip3 install pip --upgrade

RUN python -m pip install --user keras
RUN python -m pip install --user tflearn
RUN python -m pip install --user gym
RUN python -m pip install --user flake8

WORKDIR /app





