# Copyright (c) 2014
# Joey Green, School of Engineering and Computer Sciences, Durham University, UK

# All versions of this software (both binary and source) must retain
# and display this copyright notice.

# License : GPL - http://www.gnu.org/copyleft/gpl.html

# ******************** BUGGY MODULE *********************
#
# Author: Joey Green
# Date: 05/09/14
#
# Description: This module connects to the BeeWi Camera Buggy (http://www.bee-wi.com/wifi-camera-buggy-bwz200-a1-beewi,us,4,BWZ200-A1.cfm)
#   It controls it, and can pull the camera feed.
#   This module mainly uses the Python distribution of OpenCV.
#
# *******************************************************

import socket
import os, sys
import time
from video_feed import video_thread
from random import randint
from collections import Counter, deque
import cv2
import cv2.cv as cv
import numpy as np

# *********************** BUGGY CLASS *************************************

class Buggy:
    """The class to connect and control the buggy"""

    # *************** INITIALISING AND SENDING COMMANDS ************************

    EMPTY_COMMAND = bytearray([170,3,0,0,0,0,0,171])

    def __init__(self, host="192.168.11.123", image_buffer_length=15):
        """Initialisation: sets up connection and starts video feed"""
        # Start Connection
        self.HOST, self.PORT = host, 2000 # 2000 is control port
        self.wheel_angle = 0
        self.video_feed, self.sock = None, None
        self.previous_command = (0, 0)
        self.isConnected = False
        self.image_buffer, self.image_buffer_length = deque(), image_buffer_length
        
        print 'Establishing connection...'
        if self.testConnection():
            print '...connection established. Remember to exit with "exitBuggy()"!'
            # Start video feed thread (does not start streaming)
            self.startVideoThread()
            self.isConnected = True
        else:
            print '...could not establish connection. Please ensure Buggy is turned on and fully charged.'

    def testConnection(self, attempts=3):
        """Tests the connection to the buggy (default 3 attempts)"""
        # Send default command - if we receive something,
        # assume connection successful
        while attempts >= 0:
            if self.sendCommand(self.EMPTY_COMMAND):
                return True
            elif attempts == 0:
                return False
            else:
                print '...no response from Buggy. ' + str(attempts) + ' attempts left. Retrying...'
                attempts -= 1

    def sendCommand(self, data):
        """Sends raw data (bytearray) to the buggy via TCP"""
        # Open socket if not opened
        if self.sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(2)
            # Connect to server
            try:
                self.sock.connect((self.HOST, self.PORT))
            except socket.timeout:
                self.sock.close()
                return False
        # Send data
        try:
            # Send data
            self.sock.send(data)
            # Receive data from the server and shut down
            received = self.sock.recv(1024)
        except socket.timeout:
            received = None
        except:
            #print "CONNECTION ERROR"
            received = None
        # Return True if success, False if fail
        if received is not None: 
            return True
        else:
            return False

    def getPreviousCommand(self):
        """Returns the Previous command as a tuple (thrust, rotation)"""
        return self.previous_command

    # ******************************* MOVEMENT ************************************

    def move(self, thrust=0, manual_rotation=False, rotation=0):
        """Moves the buggy - takes integers for thrust and rotation,
            and a boolean for setting the manual rotation"""
        if (thrust >= 0 and thrust <= 255) and (rotation >= 0 and rotation <= 255):
            # Get angle for previous command
            if manual_rotation:
                self.sendCommand(bytearray([170,3,thrust,rotation,0,0,0,171]))
                self.previous_command = (thrust, self.commandToAngle(rotation))
            else:
                self.sendCommand(bytearray([170,3,thrust,self.wheel_angle,0,0,0,171]))
                self.previous_command = (thrust, self.commandToAngle(self.wheel_angle))
        else:
            print 'Invalid Command'

    def forward(self, speed):
        """Moves the buggy forward. Accepts values of speed between 1-100"""
        # Make sure in between 1 and 100
        if speed < 1:
            speed = 1
        elif speed > 100:
            speed = 100
        # Plus 15 for correct command
        self.move(thrust=(speed+15))
        self.previous_command = (speed, self.previous_command[1])

    def backward(self, speed):
        """Moves the buggy backward. Accepts values of speed between 1-100"""
        # Make sure in between 1 and 100
        if speed < 1:
            speed = 1
        elif speed > 100:
            speed = 100
        # Plus 143 for correct command
        self.move(thrust=(speed+143))
        self.previous_command = (-speed, self.previous_command[1])

    def turnLeft(self, value):
        """Turns the wheels left. Accepts values between 1-100"""
        # Get previous angle
        prev_value = self.previous_command[1]
        # Make sure in between 1 and 100
        if value < 1:
            value = 1
        elif value > 100:
            value = 100
        self.previous_command = (0, -value)
        # Get wait time
        wait_time = self.getWaitTime(-value, prev_value)
        # Plus 7 for correct command
        value += 7
        # Rotate manually
        self.move(manual_rotation=True,rotation=value)
        # Lock in new angle
        self.wheel_angle = value
        # Wait according to wheel difference
        time.sleep(wait_time)
        
    def turnRight(self, value):
        """Turns the wheels right. Accepts values between 1-100"""
        # Get previous angle
        prev_value = self.previous_command[1]
        # Make sure in between 1 and 100
        if value < 1:
            value = 1
        elif value > 100:
            value = 100
        self.previous_command = (0, value)
        # Get wait time
        wait_time = self.getWaitTime(value, prev_value)
        # Plus 135 for correct command
        value += 135
        # Rotate manually
        self.move(manual_rotation=True,rotation=value)
        # Lock in new angle
        self.wheel_angle = value
        # Wait according to wheel difference
        time.sleep(wait_time)

    def stop(self):
        """Stops the buggy moving"""
        self.move()

    def straightenWheels(self):
        """Makes the wheels face forward"""
        # Get previous angle
        prev_value = self.previous_command[1]
        self.previous_command = (0, 0)
        # Rotate manually
        self.move(manual_rotation=True,rotation=0)
        # Lock in 0
        self.wheel_angle = 0
        # Get wait time
        wait_time = self.getWaitTime(0, prev_value)
        # Wait according to wheel difference
        time.sleep(wait_time)
        
    # ******************************** TESTS **********************************
    
    # TESTING CONTROLLED MOVEMENT
    """NOTE: These are all very buggy (excuse the pun), as the buggy
        cannot handle multiple commands at once before it loses control"""

    def creep(self):
        self.forward(1)
        time.sleep(0.1)
        #self.backward(1)
        #time.sleep(0.01)
        self.stop()
        time.sleep(0.2)

    def creep2(self):
        self.forward(1)

    def backAway(self):
        self.backward(1)
        time.sleep(0.1)
        #self.forward(1)
        #time.sleep(0.01)
        self.stop()
        time.sleep(0.2)

    def randomisedRecovery(self, max_rotation=100, max_speed=30):
        # Random reverse
        rotation = randint(1,max_rotation)
        speed = randint(1,max_speed)
        direction = randint(0,1)
        print "Direction:", direction, "Rotation:", rotation, "Speed:", speed
        if direction:
            self.turnRight(rotation)
        else:
            self.turnLeft(rotation)
        time.sleep(0.5)
        self.backward(speed)
        time.sleep(0.8)
        self.stop()
        self.straightenWheels()
        time.sleep(0.5)

    # **************************** CAMERA FEED *********************************

    def startVideoThread(self):
        """Sets up the thread to receive the camera feed.
            Paramters: buffer_length is length of image buffer (images stored)"""
        self.video_feed = video_thread()
        try:
            self.video_feed.start()
        except SystemExit:
            self.exitBuggy()

    def closeVideoThread(self):
        """Closes the video thread"""
        try:
            self.video_feed.closeThread()
            self.video_feed.join()
        except AttributeError:
            print "No Thread to Close!"

    def streamFeed(self):
        """Starts streaming the feed. Does not display,
            but images can be extracted from the feed"""
        self.video_feed.streamFeed()

    def stopFeed(self):
        """Stops streaming the feed"""
        self.video_feed.stopFeed()

    def displayFeed(self):
        """Displays the video feed (providing it is streaming) in a window"""
        self.video_feed.displayFeed()

    def hideFeed(self):
        """Hide the displayed feed"""
        self.video_feed.hideFeed()

    def getCurrentImage(self, display=False, append=True):
        """Gets the current image from the camera feed. If display is True
            the image will be displayed in a window - else it is returned"""
        current_image = self.video_feed.getCurrentImage()
        if current_image is not None:
            if append:
                # Add to buffer
                self.addToImageBuffer(current_image)
            if display:
                cv2.namedWindow('Current Image', cv2.WINDOW_NORMAL)
                cv2.imshow('Current Image',current_image)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
            else:
                return current_image
        else:
            return None

    def addToImageBuffer(self, img):
        if img is not None:
            self.image_buffer.appendleft(img)
            # If more than required, pop
            if len(self.image_buffer) > self.image_buffer_length:
                self.image_buffer.pop()

    def clearBuffer(self):
        self.image_buffer.clear()

    def getAllImageBuffer(self):
        return self.image_buffer

    def getPreviousImage(self):
        return self.getImageFromBuffer(1)

    def getImageFromBuffer(self, index):
        try:
            return self.image_buffer[index]
        except IndexError:
            #print "Error: Image buffer empty"
            return None

    def isStuck(self, primary_t=0.9, mean_t=0.9, std_t=0.01, d=5):
        """Tests whether the buggy is stuck or not, by checking the 2 most recent
            Images. If very similar, checks image buffer for average corrolation.
            NOTE: The bigger the d, the slower it is. Use 5 for realtime applications."""
        current_image = self.getCurrentImage()
        previous_image = self.getPreviousImage()

        try:
            if current_image is not None and previous_image is not None:
                # Put both in bilateral filter
                previous_image = cv2.bilateralFilter(previous_image, d, 150, 150)
                current_image = cv2.bilateralFilter(current_image, d, 150, 150)
                # Template match
                res_match = cv2.matchTemplate(current_image,previous_image,cv2.TM_CCORR_NORMED)
                match_loc = np.where( res_match >= primary_t )
                if match_loc[0].size == 0:
                    return False
                else:
                    # Right. Investigate further. Try all image buffer to newest.
                    image_buffer = self.getAllImageBuffer()
                    correlation_list = list()
                    length = len(image_buffer)-1
                    for i in range(1, length):
                        if image_buffer[i] is not None:
                            image = cv2.bilateralFilter(image_buffer[i], d, 150, 150)
                            correlation_list.append(np.amax(cv2.matchTemplate(current_image,image,cv2.TM_CCORR_NORMED)))

                    for x in range(len(self.getAllImageBuffer()), self.image_buffer_length):
                        correlation_list.append(0)
                        
                    mean = np.mean(correlation_list)
                    std = np.std(correlation_list)
                        
                    # Finally, return
                    
                    if mean > mean_t and std < std_t:
                        # Clear buffer
                        self.clearBuffer()
                        return True
                    else:
                        return False
                return None
        except:
            # Some error
            return False
            
    # ************************* VARIOUS METHODS ************************************

    def commandToAngle(self, x):
        """Takes integer x and returns the angle of rotation"""
        if x == 0:
            return 0
        elif x > 135:
            return x - 135
        else:
            return -1* (x - 7)

    def getWaitTime(self, x, prev_x):
        return float(abs(x-prev_x))/200 # Difference of angle divided by 200 seems to work

    # *************************** EXITING **************************************

    def exitBuggy(self):
        """Exits the buggy cleanly, cleaning up video thread and
            closing the program (if being run via IDLE)"""
        # Straighten Wheels
        self.straightenWheels()
        try:
            # Video Thread
            print "Closing Video Thread..."
            self.closeVideoThread()
            print "...closed!"
            # Connection
            print "Closing Socket Connection..."
            self.sock.close()
            print "...closed!"
        finally:
            if __name__ == '__main__':
                exit()
                
# *************************** END OF CLASS *************************************

# Running the Buggy from IDLE
if __name__ == '__main__':

    # Instantiate buggy
    buggy = Buggy()

