import cv2
import time
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

motor1 = 4
motor2 = 18
motory = 22
TRIG = 17
ECHO = 27
blizu = 0
default = 0
stop = 0
vcap = 0

# tracking setup

x = 320
y = 240
cap = cv2.VideoCapture(0) # capture kamere
cap.set(3, x)  # x os
cap.set(4, y)  # y os
classNames = []
classFile = '/home/pi/Desktop/Tracking files/coco.names';
with open(classFile, 'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')
configPath = '/home/pi/Desktop/Tracking files/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt';
weightsPath = '/home/pi/Desktop/Tracking files/frozen_inference_graph.pb';
net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

# setup pogonskih motora

GPIO.setup(motor1, GPIO.OUT)
GPIO.setup(motor2, GPIO.OUT)

m1 = GPIO.PWM(motor1, 50)
m2 = GPIO.PWM(motor2, 50)

m1.start(0)
m2.start(0)

# setup motora y osi

GPIO.setup(motory, GPIO.OUT)

my = GPIO.PWM(motory, 50)

my.start(default)

# setup ultrazvučnog senzora

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# funkcije kretanja

def nul():
    m1.ChangeDutyCycle(0)
    m2.ChangeDutyCycle(0)

def fw():
    m1.ChangeDutyCycle(80)
    m2.ChangeDutyCycle(50)

def bw():
    m2.ChangeDutyCycle(80)
    m1.ChangeDutyCycle(50)

def tr():
    m2.ChangeDutyCycle(80)
    m1.ChangeDutyCycle(80)

def tl():
    m2.ChangeDutyCycle(50)
    m1.ChangeDutyCycle(50)

# program

my.ChangeDutyCycle(7)
my.ChangeDutyCycle(0)
time.sleep(5)

while True:
    succes, img = cap.read()
    classIds, confs, bbox = net.detect(img, confThreshold=0.6, nmsThreshold=0.2)
    if (len(classIds) != 0):
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            if classNames[classId - 1] == 'person':
                print(classIds, bbox)
                #cv2.rectangle(img, box, color=(0, 255, 0), thickness=(3))
                box_midx = (bbox[0, 2]/2)+bbox[0, 0]
                box_midy = (bbox[0, 3]/2)+bbox[0, 1]
                box_percentx = (box_midx/x)*100
                box_percenty = (box_midy/y)*100
                print("X os sredina:",box_midx,"Y os sredina",box_midy)
                # print ("Postotak Y: ", box_percenty)
                GPIO.output(TRIG, True)
                time.sleep(0.0001)
                GPIO.output(TRIG, False)
                while GPIO.input(ECHO) == False:
                    start = time.time()
                while GPIO.input(ECHO) == True:
                    end = time.time()
                sig_time = end-start
                distance = int(sig_time / 0.000058)  # udaljenost u cm
                print("Udaljenost: ", distance, "cm.")
                if (distance > 20) and (distance < 60) and (blizu != 1):
                    nul()
                    stop = 1
                    print("Stoji")
                if ((distance >= 30) or (distance <= 60)) and (stop == 1):
                    stop = 0
                if (box_midx == (x/2)) or (box_midy == (y/2)):
                    bw()
                    blizu = 1
                    print("Nazad")
                    time.sleep(0.1)
                    nul()
                elif (blizu == 1) and (distance >= 20):
                    blizu = 0
                if (box_percentx <= 35):
                    tl()
                    print("Lijevo")
                    #time.sleep(0.1)
                    nul()
                if (box_percentx >= 65):
                    tr()
                    print("Desno")
                    #time.sleep(0.1)
                    nul()
                if (box_percentx > 35) and (box_percentx < 65) and (blizu != 1) and (stop != 1):
                    fw()
                    print("Naprijed")
                    #time.sleep(0.1)
                    nul()
                if (box_percenty < 35):
                    my.ChangeDutyCycle(50)
                    print("Glava dolje")
                    #time.sleep(0.1)
                    my.ChangeDutyCycle(0)
                if (box_percenty > 60):
                    my.ChangeDutyCycle(80)
                    print("Glava gore")
                    #time.sleep(0.1)
                    my.ChangeDutyCycle(0)
                if (box_percenty > 35) and (box_percenty < 60):
                    my.ChangeDutyCycle(0)
                    print("Glava mirno")
                # time.sleep(0.1)
            else:
                nul()
                my.ChangeDutyCycle(default)
                print ("Nema nista")
    cv2.imshow("Output",img)
    cv2.waitKey(1)