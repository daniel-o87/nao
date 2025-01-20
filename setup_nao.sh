#!/bin/bash
# NAOqi SDK paths
export NAOQI_PATH=~/naoqi/naoqi-sdk-2.1.4.13-linux64
export PYNAOQI_PATH=~/naoqi/pynaoqi-python2.7-2.1.4.13-linux64

export PYTHONPATH=${PYNAOQI_PATH}:${PYNAOQI_PATH}/lib/python2.7/site-packages:${PYTHONPATH}
export LD_LIBRARY_PATH=${PYNAOQI_PATH}:${NAOQI_PATH}/lib:${LD_LIBRARY_PATH}


echo "PYTHONPATH = ${PYTHONPATH}"
echo "LD_LIBRARY_PATH = ${LD_LIBRARY_PATH}"


