##################
# import section #
##################
# PiCar
from picar import front_wheels, back_wheels
from picar.SunFounder_PCA9685 import Servo
import picar
# OpenCV
import cv2
# Flask
from flask import Flask, render_template, Response, request
# Time
import time
# Lane Detection
from lane_detection import lanedetect_steer


#####################
# initialize camera #
#####################
pi_camera = cv2.VideoCapture(0)

####################
# initialize picar #
####################
bw = back_wheels.Back_Wheels()   # backwheels for driving
fw = front_wheels.Front_Wheels() # front steering
pan_servo = Servo.Servo(1)       # cam horizontal
tilt_servo = Servo.Servo(2)      # cam vertical
picar.setup()                    # wake up all servos

fw.offset = 0 # offset steering
fw.turn(100)  # center steering

tilt_servo.offset = 0 # offset camera height
tilt_servo.write(90)  # move camera down for better view

bw.speed = 100  # let the car drive slowly

#################################
# initialize Monitoring Website #
#################################
app = Flask(__name__)

##################
# main functions #
##################
@app.route('/')
def index():
    return render_template('index.html')

def gen(camera):
    while True:
        # get frame from VideoCamera-instance
        ret, frame = pi_camera.read()
        if ret == False:
            print("Failed to read image")

        try:
            
            # Get steering input instruction from lanedetect_steer
            #frame, canny, steering=lanedetect_steer.lane_detection(frame,"outdoor")
            frame, canny, steering=lanedetect_steer.lane_detection(frame,"indoor")
            print('steering calc:  ' + str(steering) )
            # Give the steering instruction from lanedetect_steer to the Car-instance
            steering_value =  100 - (steering * 0.3) # initial tilt 100 minus smoothed steering score 
            print('steering value: ' + str(steering_value) )
            fw.turn(steering_value)
            
            #time.sleep(0.)

        except Exception as e:
            print("Error in detection")
            print(e)

        # Convert the processed frame to show it in the browser
        ret, frame = cv2.imencode(".jpg",frame) 
        frame = frame.tobytes()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(pi_camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def destroy(): 
    bw.stop() # stop car

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', debug=False)
    except KeyboardInterrupt:
        destroy()