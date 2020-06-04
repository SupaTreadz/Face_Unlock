# USAGE
# python recognize.py --detector face_detection_model \
#       --embedding-model openface_nn4.small2.v1.t7 \
#       --recognizer output/recognizer.pickle \
#       --le output/le.pickle --image images/adrian.jpg

# import the necessary packages
import numpy as np
import argparse
import imutils
import pickle
import cv2
import os
import time
import subprocess
import serial
from picamera import PiCamera
import smtplib 
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email import encoders 
import credentials

fromaddr = credentials.sendfrom
toaddr = credentials.sendto

camera = PiCamera()
time.sleep(3)
camera.capture('/home/pi/Face_Unlock/images/Image.jpg')

try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0)
except Exception:
    print("Warning - Serial Connection ACM0 not found")
    ser = None
else:
    print("Successful connection to Serial on ACMO")
    print(str(ser))

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True,
        help="path to input image")
ap.add_argument("-d", "--detector", required=True,
        help="path to OpenCV's deep learning face detector")
ap.add_argument("-m", "--embedding-model", required=True,
        help="path to OpenCV's deep learning face embedding model")
ap.add_argument("-r", "--recognizer", required=True,
        help="path to model trained to recognize faces")
ap.add_argument("-l", "--le", required=True,
        help="path to label encoder")
ap.add_argument("-c", "--confidence", type=float, default=0.5,
        help="minimum probability to filter weak detections")
args = vars(ap.parse_args())

# load our serialized face detector from disk
print("[INFO] loading face detector...")
protoPath = os.path.sep.join([args["detector"], "deploy.prototxt"])
modelPath = os.path.sep.join([args["detector"],
        "res10_300x300_ssd_iter_140000.caffemodel"])
detector = cv2.dnn.readNetFromCaffe(protoPath, modelPath)

# load our serialized face embedding model from disk
print("[INFO] loading face recognizer...")
embedder = cv2.dnn.readNetFromTorch(args["embedding_model"])

# load the actual face recognition model along with the label encoder
recognizer = pickle.loads(open(args["recognizer"], "rb").read())
le = pickle.loads(open(args["le"], "rb").read())

speech = "Starting facial reconition"
subprocess.call(['/home/pi/Face_Unlock/speech.sh',speech])

# load the image, resize it to have a width of 600 pixels (while
# maintaining the aspect ratio), and then grab the image dimensions
while True:
    if ser is None:
        try:
            ser = serial.Serial('/dev/ttyACM0', 115200, write_timeout=0, timeout=0)
        except Exception:
            print("Warning - Serial Connection ACM0 not found")
            ser = None
        else:
            print("Successful connection to Serial on ACMO")
    else:
        ser.write(str.encode("heartbeat"))
    #time.sleep(2)
    image = cv2.imread(args["image"])
    image = imutils.resize(image, width=600)
    (h, w) = image.shape[:2]

    # construct a blob from the image
    imageBlob = cv2.dnn.blobFromImage(
            cv2.resize(image, (300, 300)), 1.0, (300, 300),
            (104.0, 177.0, 123.0), swapRB=False, crop=False)

    # apply OpenCV's deep learning-based face detector to localize
    # faces in the input image
    detector.setInput(imageBlob)
    detections = detector.forward()

    # loop over the detections
    for i in range(0, detections.shape[2]):
            # extract the confidence (i.e., probability) associated with the
            # prediction
            confidence = detections[0, 0, i, 2]

            # filter out weak detections
            if confidence > args["confidence"]:
                    # compute the (x, y)-coordinates of the bounding box for the
                    # face
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")

                    # extract the face ROI
                    face = image[startY:endY, startX:endX]
                    (fH, fW) = face.shape[:2]

                    # ensure the face width and height are sufficiently large
                    if fW < 20 or fH < 20:
                            continue

                    # construct a blob for the face ROI, then pass the blob
                    # through our face embedding model to obtain the 128-d
                    # quantification of the face
                    faceBlob = cv2.dnn.blobFromImage(face, 1.0 / 255, (96, 96),
                            (0, 0, 0), swapRB=True, crop=False)
                    embedder.setInput(faceBlob)
                    vec = embedder.forward()

                    # perform classification to recognize the face
                    preds = recognizer.predict_proba(vec)[0]
                    j = np.argmax(preds)
                    proba = preds[j]
                    name = le.classes_[j]
                    if str(name) == "sam":
                        print("True")
                        print(str(confidence))
                        percent_confidence = round(confidence * 100,1)
                        speech = "I am " + str(percent_confidence) + "% sure you are Sam"
                        speech2 = "Welcome home, Sam"
                        string1 = "unlock "
                        string1e = string1.encode()
                        print(string1e)
                        try:
                            ser.write(string1e)
                        except Exception:
                            print("Error sending data")
                            speech = "data transmission error"
                            subprocess.call(['/home/pi/Face_Unlock/speech.sh',speech])
                        else:
                            print("unlock command sent")
                        subprocess.call(['/home/pi/Face_Unlock/speech.sh',speech])
                        subprocess.call(['/home/pi/Face_Unlock/speech.sh',speech2])
                    else:
                        print("Unrecognized")
                        speech = "I don't recognize your face"
                        subprocess.call(['/home/pi/Face_Unlock/speech.sh',speech])

                    # draw the bounding box of the face along with the associated
                    # probability
                    text = "{}: {:.2f}%".format(name, proba * 100)
                    y = startY - 10 if startY - 10 > 10 else startY + 10
                    cv2.rectangle(image, (startX, startY), (endX, endY),
                            (0, 0, 255), 2)
                    cv2.putText(image, text, (startX, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)
                    
                    #write out image result for email
                    cv2.imwrite("CV2_Result.png",image);
                    
                    msg = MIMEMultipart() 
                    msg['From'] = fromaddr 
                    msg['To'] = toaddr 
                    msg['Subject'] = "Face Unlock"
                    body = "Door Unlocked"
                    msg.attach(MIMEText(body, 'plain')) 
                    filename = "C2V_Result.png"
                    attachment = open("/home/pi/Face_Unlock/CV2_Result.png", "rb") 
                    p = MIMEBase('application', 'octet-stream') 
                    p.set_payload((attachment).read()) 
                    encoders.encode_base64(p) 
                    p.add_header('Content-Disposition', "attachment; filename= %s" % filename) 
                    msg.attach(p) 
                    s = smtplib.SMTP('smtp.gmail.com', 587) 
                    s.starttls() 
                    s.login(fromaddr, credentials.password) 
                    text = msg.as_string() 
                    s.sendmail(fromaddr, toaddr, text) 
                    s.quit() 

    camera.capture('/home/pi/Face_Unlock/images/Image.jpg')
    print("new capture")

    # show the output image
    #cv2.imshow("Image", image)
    #cv2.waitKey(0)
