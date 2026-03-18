import cv2
import time
import RPi.GPIO as GPIO
import numpy as np

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

motorlf = 14
motorlb = 15
motorrf = 23
motorrb = 24
motory = 18
TRIG = 17
ECHO = 27
blizu = 0
default = 7
stop = 0
x_mid=0
y_mid=0
x=1
y=1
w=0
h=0
p=0
p2=0
p3=0
position=7
value = 50
x_pos = 0

# setup pokretačke sklopke

GPIO.setup(26,GPIO.IN,pull_up_down=GPIO.PUD_UP)

# tracking setup

cap = cv2.VideoCapture(0)
cap.set(3,640)
cap.set(4,480)

# setup pogonskih motora

GPIO.setup(motorlf, GPIO.OUT)
GPIO.setup(motorlb, GPIO.OUT)
GPIO.setup(motorrf, GPIO.OUT)
GPIO.setup(motorrb, GPIO.OUT)

mlf = GPIO.PWM(motorlf, 50)
mlb = GPIO.PWM(motorlb, 50)
mrf = GPIO.PWM(motorrf, 50)
mrb = GPIO.PWM(motorrb, 50)

mlf.start(0)
mlb.start(0)
mrf.start(0)
mrb.start(0)

# setup motora y osi

GPIO.setup(motory, GPIO.OUT)

my = GPIO.PWM(motory, 50)

my.start(default)

# setup ultrazvučnog senzora

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# funkcije kretanja

def nul():
    mlf.ChangeDutyCycle(0)
    mlb.ChangeDutyCycle(0)
    mrf.ChangeDutyCycle(0)
    mrb.ChangeDutyCycle(0)

def fw():
    mlf.ChangeDutyCycle(value)
    mlb.ChangeDutyCycle(0)
    mrf.ChangeDutyCycle(value)
    mrb.ChangeDutyCycle(0)

def bw():
    mlf.ChangeDutyCycle(0)
    mlb.ChangeDutyCycle(value)
    mrf.ChangeDutyCycle(0)
    mrb.ChangeDutyCycle(value)

def tl(r):
    mlf.ChangeDutyCycle(0)
    mlb.ChangeDutyCycle(r)
    mrf.ChangeDutyCycle(r)
    mrb.ChangeDutyCycle(0)

def tr(r):
    mlf.ChangeDutyCycle(r)
    mlb.ChangeDutyCycle(0)
    mrf.ChangeDutyCycle(0)
    mrb.ChangeDutyCycle(r)

# program

while True:

    while (GPIO.input(26)==0):
        _, frame = cap.read()
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        #finding nemo
        low_orang = np.array([7,150,150])
        high_orang = np.array([25,255,255])
        orange_mask= cv2.inRange(hsv_frame, low_orang, high_orang)
        orange= cv2.bitwise_and (frame, frame, mask=orange_mask)
        contours, _ = cv2.findContours(orange_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=lambda x:cv2.contourArea(x), reverse=True)

        for cnt in contours:
            (x, y, w, h) = cv2.boundingRect(cnt)
            if (w>=80) and (h>=80):
                cv2.rectangle(frame, (x,y), (x+w, y+h), (0, 255, 0), 2)
                x_mid = int((x+x+w)/2)
                y_mid = int((y+y+h)/2)
                cv2.line(frame,(x_mid,0),(x_mid,480),2)
                cv2.line(frame,(0,y_mid),(640,y_mid),2)
            break
        if (w>=80) and (h>=80):
            if (x==0):
                x=1
            if (y==0):
                y=1
            if (w==p):
                p2+=1
            elif (w!=p):
                p2=0
                p3=0
            print("Pomocna:", p2)
            if (p2>=10):
                p3=1
            p=w
            print("Y:", y, "H:",h)
            print("Position: ", position)
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
            if (((distance <= 30) or (distance >= 60))) and (stop == 1):
                stop = 0
            if (distance <=20):
                bw()
                blizu = 1
            elif (blizu == 1) and (distance >= 20):
                blizu = 0
            if (x_mid <= 280):
                x_pos = 20 + (x_mid/10)
                tl(x_pos)
            if (x_mid >= 360):
                x_pos = 20 + ((x_mid-360)/10)
                tr(x_pos)
            if (x_mid > 280) and (x_mid < 360) and (blizu != 1) and (stop != 1):
                fw()
            if (y_mid<=210):
                position -= ((y_mid/1000))
                print("Glava gore")
            if (y_mid>=270):
                position += (((y_mid-270)/1000))
                print("Glava dolje")
            if (position>=12):
                position=12
            if (position<=2):
                position=2
            my.ChangeDutyCycle(position)
        if (p3==1) or (w<80) or (h<80):
            nul()
            my.ChangeDutyCycle(0)
            print ("Nema nista")
        cv2.imshow("Output",frame)
        cv2.waitKey(1)