# Project Setup Guide

To ensure smooth execution, you will need to set up two virtual environments: one for Python 2.7 and another for Python 3.x. Below are the steps to create and manage these environments.

## 1. Setting up the Python 2.7 Virtual Environment

This environment is used for the NAO robot control scripts.

1. Install virtualenv for Python 2.7 (if not already installed):
   ```
   pip install virtualenv
   ```

2. Create the virtual environment:
   ```
   virtualenv -p /usr/bin/python2.7 ~/robot_py27_env
   ```

3. Activate the environment:
   ```
   source ~/robot_py27_env/bin/activate
   ```

4. Install the required dependencies:
   ```
   pip install -r requirements_py27.txt
   ```

## 2. Setting up the Python 3.x Virtual Environment

This environment is for running YOLO and TensorFlow Lite models.

1. Install virtualenv for Python 3.x:
   ```
   pip3 install virtualenv
   ```

2. Create the virtual environment:
   ```
   python3 -m venv ~/yolo_py3_env
   ```

3. Activate the environment:
   ```
   source ~/yolo_py3_env/bin/activate
   ```

4. Install the required dependencies:
   ```
   pip install ultralytics tensorflow flask opencv-python
   ```

## 3. Running the Project

You will need two terminals for this project—one for controlling the NAO robot and one for running the YOLO and TensorFlow Lite models.

### Terminal 1: NAO Robot Control

Activate the Python 2.7 environment for the NAO robot and run the control script.

```
source ~/robot_py27_env/bin/activate
python2.7 main.py
```

### Terminal 2: YOLO and TensorFlow Lite

Activate the Python 3.x environment for YOLO and TensorFlow Lite, and run the server.

```
source ~/yolo_py3_env/bin/activate
python3 tflite_server.py
```



You also need a directory named models where you will put the yolo_x.pn and 
