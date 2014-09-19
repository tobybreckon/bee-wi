# Copyright (c) 2014
# Joey Green, School of Engineering and Computer Sciences, Durham University, UK

# All versions of this software (both binary and source) must retain
# and display this copyright notice.

# License : GPL - http://www.gnu.org/copyleft/gpl.html

# ******************* IMAGE FOLLOWER MODULE *********************
#
# Author: Joey Green
# Date: 05/09/14
#
# Description: This module uses the Buggy module, and allows the Buggy to
#   follow / move away from images in red circles.
#
# ***************************************************************

import cv2
import cv2.cv as cv
import time
import numpy as np
from matplotlib import pyplot as plt
from buggy import Buggy
from scipy import ndimage
import sys

# ********************** VARIABLES **********************
#
# Modify these to tailor to your environment.
#

# Set up signs for template matching
SIGN_FORWARD = ndimage.median_filter(cv2.imread('C:\\Users\\Joey\\Documents\\Work\\Year_3\\Internship\\Template_Matching\\Arrows\\Up_and_Down\\up.png', 0), 5)
SIGN_BACKWARD = ndimage.median_filter(cv2.imread('C:\\Users\\Joey\\Documents\\Work\\Year_3\\Internship\\Template_Matching\\Arrows\\Up_and_Down\\down.png', 0), 5)

BINARY_THRESHOLD = 120 # This is the threshold for the Binary Threshing within the cropped image of the sign

MATCH_THRESHOLD = 0.3 # The treshold for the template matching of the signs

DISPLAY = True # Whether you want to display what the Buggy sees

# *******************************************************

# ******************** LOCAL FUNCTIONS ******************

def wait():
    time.sleep(0.01)

# *****************************************************

# ******************* PROGRAM *************************

# Instantiate Buggy
buggy = Buggy()

# If connected
if buggy.isConnected:

    # Stream the feed
    buggy.streamFeed()

    # Wait for feed to start...
    wait()

    # Loop
    try:

        if DISPLAY:
            cv2.namedWindow('display_image',cv2.WINDOW_NORMAL)
            cv2.namedWindow('chroma_red',cv2.WINDOW_NORMAL)
            cv2.namedWindow('detected_circles',cv2.WINDOW_NORMAL)
            cv2.namedWindow('cropped_image',cv2.WINDOW_NORMAL)
            cv2.namedWindow('template_match',cv2.WINDOW_NORMAL)

        # Get initial crop image
        crop_img = np.zeros((200,200,3), np.uint8)

        # create a CLAHE object (Arguments are optional).
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))

        # Set some variables for movement and turning
        moving_status = "stopped"
        wheel_direction = "neutral"

        while True:
            
            # Get current Image
            current_image = buggy.getCurrentImage()
            while current_image is None:
                current_image = buggy.getCurrentImage()
            display_image = current_image.copy()

            # YCrCb
            YCrCb = cv2.cvtColor(current_image, cv2.COLOR_BGR2YCR_CB)

            # Split to get Chroma_red
            Chroma_red = YCrCb[:,:,1]

            _, Chroma_red = cv2.threshold(Chroma_red,135,255,cv2.THRESH_BINARY)
            
            # Circles
            try:
                circles = cv2.HoughCircles(Chroma_red,cv.CV_HOUGH_GRADIENT,1,300,
                                param1=50,param2=30,minRadius=0,maxRadius=0)
                circles = np.uint16(np.around(circles))

                if len(circles[0,:]): # If detected a circle:

                    # Set up coordinates
                    i = circles[0,0,:]
                    circle_x, circle_y = i[0], i[1]
                    
                    # draw the outer circle
                    cv2.circle(current_image,(i[0],i[1]),i[2],(0,255,0),2)
                    # draw the center of the circle
                    cv2.circle(current_image,(i[0],i[1]),2,(0,0,255),3)

                    y1 = 0 if i[1] < i[2] else i[1]-i[2]
                    x1 = 0 if i[0] < i[2] else i[0]-i[2] # TO AVOID OVERFLOW (using ushort_scalars)
                    y2, x2 = i[1]+i[2], i[0]+i[2] # These are the points of the cropped image

                    # Crop image
                    crop_img = display_image[y1:y2, x1:x2]
                    # Resize it to 200x200
                    crop_img = cv2.resize(crop_img, (290, 290))
                    # To Black and White
                    crop_img = cv2.cvtColor(crop_img,cv2.COLOR_BGR2GRAY)

                    # Threshing
                    _, crop_img = cv2.threshold(crop_img,BINARY_THRESHOLD,255,cv2.THRESH_BINARY)
           
                    # Otsu Threshing
                    #_, crop_img = cv2.threshold(crop_img,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
                    # Median Filter (for excess noise)
                    crop_img = ndimage.median_filter(crop_img, 5)

                    # Result
                    max_res_SIGN_FORWARD = np.amax(cv2.matchTemplate(crop_img,SIGN_FORWARD,cv2.TM_CCOEFF_NORMED))
                    max_res_SIGN_BACKWARD = np.amax(cv2.matchTemplate(crop_img,SIGN_BACKWARD,cv2.TM_CCOEFF_NORMED))

                    """ DETECTING SIGNS """
                    turn_angle = circle_x
                    while turn_angle > 160:
                        turn_angle -= 160
                    turn_angle = 100 - int(round((float(turn_angle)/160)*100))
                    
                    if max_res_SIGN_FORWARD >= max_res_SIGN_BACKWARD and max_res_SIGN_FORWARD >= MATCH_THRESHOLD:
                        # Turn towards it
                        if circle_x > 170:
                            print 'circle_x', circle_x, 'turning right', turn_angle
                            buggy.turnRight(turn_angle)
                        elif circle_x < 150:
                            print 'circle_x', circle_x, 'turning left', turn_angle
                            buggy.turnLeft(turn_angle)
                        # Change Status
                        moving_status = "forward"
                        
                    elif max_res_SIGN_BACKWARD >= max_res_SIGN_FORWARD and max_res_SIGN_BACKWARD >= MATCH_THRESHOLD:
                        # Turn away from it
                        if circle_x > 170:
                            print 'circle_x', circle_x, 'turning left', turn_angle
                            buggy.turnLeft(turn_angle)
                        elif circle_x < 150:
                            print 'circle_x', circle_x, 'turning right', turn_angle
                            buggy.turnRight(turn_angle)
                        # Change Status
                        moving_status = "backward"
                        
                    else:
                        # Can't recognise sign
                        print "Don't recognise sign"
                else:
                    # No circles detected
                    pass
                        
            except:
                #print "Something went wrong..."
                pass
            
            """ MOVING THE BUGGY (Don't delete!) """
            if moving_status is "forward" or moving_status is "backward":
                # Move in direction
                if moving_status is "forward":
                    buggy.creep()
                elif moving_status is "backward":
                    buggy.backAway()
                # Reset moving_status flag
                moving_status = "stopped"
                
            """ DISPLAYING IMAGE """
            if DISPLAY:

                # Show
                try:
                    cv2.imshow('display_image',display_image)
                except:
                    pass
                try:
                    cv2.imshow('chroma_red',Chroma_red)
                except:
                    pass
                try:
                    cv2.imshow('detected_circles',current_image)
                except:
                    pass
                try:
                    cv2.imshow('cropped_image',crop_img)
                except:
                    pass
                try:
                    if loc_SIGN_FORWARD[1].any():
                        cv2.imshow('template_match', SIGN_FORWARD)
                    elif loc_SIGN_BACKWARD[1].any():
                        cv2.imshow('template_match', SIGN_BACKWARD)
                except:
                    pass

                # To quit
                k = cv2.waitKey(33)
                if k==27:    # Esc key to stop
                    cv2.destroyAllWindows()
                    break

    except KeyboardInterrupt:
        print "Keyboard Interrupt Detected!"

    finally:
        # Stop the video feed
        buggy.exitBuggy()
        #exit()
