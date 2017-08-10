import pyrebase
from twilio.rest import Client
from detector import Detector
import RPi.GPIO as GPIO
import time
import picamera
import sys, os
import json, http.client
from datetime import datetime
import base64
import threading

# Setting up Pi with Firebase
config = {
    "apiKey": "FIREBASE_API_KEY",
    "authDomain": "APP_ID.firebaseapp.com",
    "databaseURL": "https://APP_ID.firebaseio.com",
    "storageBucket": "APP_ID.appspot.com"
    }
firebase = pyrebase.initialize_app(config)

# Initializing Firebase
auth = firebase.auth()
user = auth.sign_in_with_email_and_password("E_MAIL","PASS")
storage = firebase.storage()
db = firebase.database()
print ("Connected to Firebase")


# Twilio SMS config
accountSID = "ACCOUNT_SID"
authToken = "AUTH_TOKEN"
client = Client(accountSID, authToken)
myTwilioNumber = "YOUR_TWILIO_NUMBER"
myCellPhone = "CELL_PHONE_NUMBER"

# PIR sensor config with Raspberry Pi
sensor = 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(sensor, GPIO.IN, GPIO.PUD_DOWN)

previous_state = False
current_state = False

# Start time when script starts
refreshTimer = time.time()

# Initialize Pi camera
cam = picamera.PiCamera()
lock = threading.Lock()

 
# Camera Settings
imgCount   = 5
frameSleep = 0.5    # Seconds between burst-snaps
camSleep   = 1      # Seconds between Detections

def _error(m):
    print(m)

def is_person(image):
    det = Detector(image)
    faces = len(det.face())
    print ("FACE: ", det.drawColors[det.drawn-1 % len(det.drawColors)], faces)
    uppers = len(det.upper_body())
    print ("UPPR: ", det.drawColors[det.drawn-1 % len(det.drawColors)], uppers)
    fulls = len(det.full_body())
    print ("FULL: ", det.drawColors[det.drawn-1 % len(det.drawColors)], fulls)
    lowers = len(det.lower_body())
    print ("LOWR: ", det.drawColors[det.drawn-1 % len(det.drawColors)], lowers)

    det.draw()
   
    return faces + uppers + fulls + lowers

def processImage(filename):
    if is_person(filename):
        print ("True")
        lock.acquire()
        try:
            # Uploading image to Firebase
            message = client.messages.create(to="CELL_PHONE_NUMBER", from_="TWILIO_NUMBER", body="Intruder Alert!")
            print ("SMS successfully sent to User")
            storage.child("users").child("USER_CHILD_ID").child("%s" % filename).put(filename, user['idToken'])
            url = storage.child("users").child("USER_CHILD_ID").child("%s" % filename).get_url(None)
            data = {
                "image_link":url
                }
            db.child("users").child("USER_CHILD_ID").update(data, user['idToken'])
            
            print ("Photo Uploaded!")
        except:
            print ("Error Uploading.")
        lock.release()
        
    else:   # Not a person
        print ("False")
        os.remove(filename)
    sys.exit(0) 

try:  
    while True:
        previous_state = current_state
        currentTime = time.time()
        
        # Our current state is set to our PIR sensor state
        current_state = GPIO.input(sensor)

        # Refresh Firebase user-token
        if (currentTime - refreshTimer) >= 1800:
            user = auth.refresh(user["refreshToken"])
            refreshTimer = currentTime
            print("token refresh: %s" % (time.strftime("%c")))

        if current_state != previous_state:
        # If our PIR sensor state changes
            new_state = "HIGH" if current_state else "LOW"

            # Then we know motion has been detected
            if current_state:     # Motion is Detected
                lock.acquire()
                #Lets turn on camera preview to get a glimpse of what the cam is capturing
                cam.start_preview()
                cam.preview_fullscreen = False
                cam.preview_window = (10,10, 320,240)
                print('Motion Detected')
                
                for i in range(imgCount):
                # Set a variable with the current time to use as image file name
                    curTime = (time.strftime("%I:%M:%S")) + ".jpg"
                # The captures, names and resizes a photo.
                    cam.capture(curTime, resize=(320,240))
                    t = threading.Thread(target=processImage, args=[curTime])
                    t.daemon = True
                    t.start()
                    time.sleep(frameSleep)
                # Now turn off the camera preview after capturing
                cam.stop_preview()
                lock.release()
                time.sleep(camSleep)

# If we interrupt main thread with a Keyboard Interrupt
except KeyboardInterrupt:
  # Turn off any camera preview
  cam.stop_preview()
  sys.exit(0)
