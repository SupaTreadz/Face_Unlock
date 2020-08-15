#!/bin/bash

python3 /home/pi/Face_Unlock/recognize.py --detector /home/pi/Face_Unlock/face_detection_model --embedding-model /home/pi/Face_Unlock/openface_nn4.small2.v1.t7 --recognizer /home/pi/Face_Unlock/output/recognizer.pickle --le /home/pi/Face_Unlock/output/le.pickle --image /home/pi/Face_Unlock/images/Image.jpg
