# Copyright (c) 2014
# Joey Green, School of Engineering and Computer Sciences, Durham University, UK

# All versions of this software (both binary and source) must retain
# and display this copyright notice.

# License : GPL - http://www.gnu.org/copyleft/gpl.html

# ******************** PATH FOLLOWER MODULE *********************
#
# Author: Joey Green
# Date: 05/09/14
#
# Description: This module uses the Buggy module, and allows the Buggy to
#   follow red signs containing arrows placed on the floor.
#
# ***************************************************************

import sys
import cv2
import cv2.cv as cv
import time
import numpy as np
from matplotlib import pyplot as plt
from scipy import ndimage
sys.path.append('../sdk')
from buggy import Buggy

# ********************** VARIABLES **********************
#
# Modify these to tailor to your environment.
#

DETECT_FLOOR, DETECT_WALL = True, False # Whether to detect signs on the floor and/or wall (at least one must be True!)

MAX_RECOGNISING_COUNT = 20 # The higher this is, the more accurate and slower it will be
MAX_TURN_STEPS = 1 # How many times the buggy continues turning after a sign

# The file location of the picture of the CROSS (X) to make the Buggy STOP
PATH_CROSS = '..\\doc\\symbols\\cross_simple.png'
# The number of arrow images (usually an odd number - left, right and forward)
NUMBER_OF_ARROWS = 13
# The path to the directory that contains the arrows for turning the Buggy (must be labelled from 00)
PATH_ARROW_FOLDER = '..\\doc\\symbols\\15_step\\'

if DETECT_FLOOR: # Image and Object Points to warp the camera perspective for detecting signs on the floor
    PATH_IMAGE_POINTS = '..\\doc\\imagePoints\\imgPts.npy'
    PATH_OBJECT_POINTS = '..\\doc\\imagePoints\\objPts.npy'

CHROMA_RED_THRESHOLD = 130 # The threshold to use in binary threshing of the Chroma Red Channel (default 135)

DISPLAY = True # Whether you want to display what the Buggy sees
    
# *******************************************************

5# ******************** LOCAL FUNCTIONS ******************
def wait():
    time.sleep(0.01)

def mean(nums):
    if len(nums):
        return int( round(float(sum(nums)) / len(nums)))
    else:
        return 0

def follow_arrow_direction(best_arrow, moving_forward, wheel_direction, arrow_buffer):
    # Left
    if best_arrow < (NUMBER_OF_ARROWS//2):
        print '{0} Match: {1} degrees Left'.format(str(best_result)[:5], 90-(ARROW_DEGREE_DIFF*best_arrow))
        wheel_direction = "left"
        buggy.turnLeft(90-(ARROW_DEGREE_DIFF*best_arrow))
    # Right
    elif best_arrow > (NUMBER_OF_ARROWS//2):
        print '{0} Match: {1} degrees Right'.format(str(best_result)[:5], 90-(ARROW_DEGREE_DIFF*(NUMBER_OF_ARROWS-best_arrow-1)))
        wheel_direction = "right"
        buggy.turnRight(90-(ARROW_DEGREE_DIFF*(NUMBER_OF_ARROWS-best_arrow-1)))
    # Forward
    else:
        print '{0} Match: Straight Forward'.format(str(best_result)[:5])
        if wheel_direction is not "neutral":
            wheel_direction = "neutral"
            buggy.straightenWheels()

    confident_match = True if best_result > 0.2 else False # Will only move forward fast if confident
    moving_forward = True
    del arrow_buffer[:]

    return moving_forward, wheel_direction, confident_match, arrow_buffer

# *****************************************************

# ******************* PROGRAM *************************

# Instantiate Buggy
buggy = Buggy()

# If connected
if buggy.isConnected:

    # Set up signs for template matching
    sign_cross = cv2.imread(PATH_CROSS, 0)
    # Get image resolution from this
    IMAGE_RESOLUTION_w, IMAGE_RESOLUTION_h = sign_cross.shape[::-1]
    # Arrows
    arrow_list = list()
    ARROW_DEGREE_DIFF = 180//(NUMBER_OF_ARROWS-1)
    for i in range(NUMBER_OF_ARROWS):
        index_string = str(i)
        if len(index_string) == 1:
            index_string = '0' + index_string
        arrow_list.append(ndimage.median_filter(cv2.imread(PATH_ARROW_FOLDER + index_string + '.png', 0), 5))

    # Set up matrix and stuff
    if DETECT_FLOOR:
        imgPts = np.load(PATH_IMAGE_POINTS)
        objPts = np.load(PATH_OBJECT_POINTS)
        resolution = (640,480)
        H, mask = cv2.findHomography(imgPts, objPts)

    # Get initial crop image
    crop_img = np.zeros((320,240,3), np.uint8)

    # create a CLAHE object (Arguments are optional).
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))

    # Set some variables for movement and turning
    moving_forward, wait_once, creep_once, confident_match = False, False, False, False
    wheel_direction = "neutral"
    arrow_buffer = list()
    turn_counter = 0

    # Stream the feed
    buggy.streamFeed()

    # Wait for feed to start...
    wait()

    # Loop
    try:

        if DISPLAY:
            cv2.namedWindow('detected_circles',cv2.WINDOW_NORMAL)       
            cv2.namedWindow('cropped_image',cv2.WINDOW_NORMAL)
            cv2.namedWindow('best_match',cv2.WINDOW_NORMAL)
            if DETECT_WALL:
                cv2.namedWindow('Chroma_red_normal',cv2.WINDOW_NORMAL)
            if DETECT_FLOOR:
                cv2.namedWindow('birds_eye',cv2.WINDOW_NORMAL)
                cv2.namedWindow('Chroma_red_birds',cv2.WINDOW_NORMAL)

        while True:
            
            # Get current Image
            current_image = buggy.getCurrentImage()
            while current_image is None:
                current_image = buggy.getCurrentImage()
            display_image = np.copy(current_image)

            try:

                # Set circles to None
                circles = None
                circle_on_floor = False
                
                # DETECT ON FLOOR (priority if both checked)
                if DETECT_FLOOR:

                    # Get birds eye Perspective
                    birds_eye_Homography = cv2.warpPerspective(current_image, H, resolution, cv.CV_INTER_LINEAR | cv.CV_WARP_INVERSE_MAP | cv.CV_WARP_FILL_OUTLIERS)
                    birds_eye_copy = np.copy(birds_eye_Homography)

                    # YCrCb
                    YCrCb = cv2.cvtColor(birds_eye_Homography, cv2.COLOR_BGR2YCR_CB)
                    Chroma_red = YCrCb[:,:,1]

                    # Threshold it
                    _, Chroma_red = cv2.threshold(Chroma_red,CHROMA_RED_THRESHOLD,255,cv2.THRESH_BINARY)

                    # Blur it to remove noise
                    Chroma_red = ndimage.median_filter(Chroma_red, 9)

                    try:
                        # Circles
                        circles = cv2.HoughCircles(Chroma_red,cv.CV_HOUGH_GRADIENT,1,300,
                                        param1=40,param2=20,minRadius=30,maxRadius=100)
                        circles = np.uint16(np.around(circles))
                        # Set circle found on floor
                        circle_on_floor = True
                    except:
                        pass  
                
                # If set to detect walls, and has not found any circles
                if DETECT_WALL and (circles is None or not len(circles[0,:])):

                    # YCrCb
                    YCrCb2 = cv2.cvtColor(current_image, cv2.COLOR_BGR2YCR_CB)
                    Chroma_red_normal = YCrCb2[:,:,1]
                    
                    # Threshold it
                    _, Chroma_red_normal = cv2.threshold(Chroma_red_normal,CHROMA_RED_THRESHOLD,255,cv2.THRESH_BINARY)

                    # Blur it to remove noise
                    Chroma_red_normal = ndimage.median_filter(Chroma_red_normal, 9)
                    
                    try:
                        # Circles
                        circles = cv2.HoughCircles(Chroma_red_normal,cv.CV_HOUGH_GRADIENT,1,300,
                                        param1=40,param2=20,minRadius=0,maxRadius=0)
                        circles = np.uint16(np.around(circles))
                        # Set circle found on wall
                        circle_on_floor = False
                    except:
                        pass

                        
                if len(circles[0,:]): # If detected a circle:

                    # Grab the circle as a variable
                    i = circles[0,0,:]
                    circle_x, circle_y = i[0], i[1]
                    
                    y1 = 0 if i[1] < i[2] else i[1]-i[2]
                    x1 = 0 if i[0] < i[2] else i[0]-i[2] # TO AVOID OVERFLOW (using ushort_scalars)
                    y2, x2 = i[1]+i[2], i[0]+i[2] # These are the points of the cropped image

                    # Draw Circle and get cropped sign (depending if on wall or floor)
                    if circle_on_floor:
                        # draw the outer circle
                        cv2.circle(birds_eye_copy,(i[0],i[1]),i[2],(0,255,0),2)
                        # draw the center of the circle
                        cv2.circle(birds_eye_copy,(i[0],i[1]),2,(0,0,255),3)                  
                        # Get actualy crop image
                        crop_img_rgb = birds_eye_Homography[y1:y2, x1:x2]
                    else:
                        # draw the outer circle
                        cv2.circle(display_image,(i[0],i[1]),i[2],(0,255,0),2)
                        # draw the center of the circle
                        cv2.circle(display_image,(i[0],i[1]),2,(0,0,255),3)                  
                        # Get actualy crop image
                        crop_img_rgb = current_image[y1:y2, x1:x2]

                    
                    crop_img_rgb = cv2.resize(crop_img_rgb, (IMAGE_RESOLUTION_w, IMAGE_RESOLUTION_h))
                    crop_img_rgb = cv2.cvtColor(crop_img_rgb,cv2.COLOR_BGR2GRAY)
                    _, crop_img_rgb = cv2.threshold(crop_img_rgb,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
                    crop_img_rgb = ndimage.median_filter(crop_img_rgb, 5)

                    # Threshold
                    cross_threshold = 0.7
                    
                    # Cross Result
                    res_cross = cv2.matchTemplate(crop_img_rgb,sign_cross,cv2.TM_CCOEFF_NORMED)
                    # Find location
                    loc_cross = np.where( res_cross >= cross_threshold )

                    if loc_cross[1].any():
                        # Stop (if not already stationary)
                        if wheel_direction is not "neutral":
                            wheel_direction = "neutral"
                            buggy.straightenWheels()
                        if moving_forward:
                            print "Stopping!"
                            moving_forward = False
                        del arrow_buffer[:]
                            
                    else:

                        # If y at high point, don't move (optimum position)
                        if not circle_on_floor or circle_y > 350:

                            # Try all the arrows
                            best_result = 0
                            best_arrow = None
                            for i in range(NUMBER_OF_ARROWS):
                                # Arrow Result
                                max_res_arrow = np.amax(cv2.matchTemplate(crop_img_rgb,arrow_list[i],cv2.TM_CCOEFF_NORMED))
                                if max_res_arrow > best_result:
                                    best_result = max_res_arrow
                                    best_arrow = i
                            
                            # Add best value to arrow buffer
                            if best_arrow is not None:
                                arrow_buffer.append(best_arrow)
                            # If more than MAX, go with average
                            if len(arrow_buffer) >= MAX_RECOGNISING_COUNT:
                                print "Taking average arrow direction...", arrow_buffer
                                best_arrow = mean(arrow_buffer)
                                # Follow arrow
                                moving_forward, wheel_direction, confident_match, arrow_buffer = follow_arrow_direction(best_arrow, moving_forward, wheel_direction, arrow_buffer)
                                buggy.clearBuffer() # Moved, so clear the buffer
                            else:
                                if len(arrow_buffer) == 1:
                                    print "Learning direction of arrow..."
                                wait_once = True
                        else:
                            # Move towards sign
                            print "Moving towards sign..."
                            if circle_x > 160:
                                buggy.turnRight((circle_x/320)*100)
                            else:
                                buggy.turnLeft((circle_x/160)*100)
                            creep_once, moving_forward = True, False
                else:
                    # Move towards largest contour
                    # Countours (already threshed)
                    contours, hierarchy = cv2.findContours(Chroma_red, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
                    # Find the index of the largest contour
                    areas = [cv2.contourArea(c) for c in contours]
                    if areas:
                        max_index = np.argmax(areas)
                        cnt = contours[max_index]
                        # Straight Bounding Rectangle
                        x,y,w,h = cv2.boundingRect(cnt)
                        center_x = x + w/2
                        # Display bounding box on chroma red channel
                        cv2.rectangle(Chroma_red,(x,y),(x+w,y+h),(0,255,0),2)
                        # Move towards sign
                        print "Moving towards red object..."
                        if center_x > 160:
                            buggy.turnRight((center_x/320)*100)
                        else:
                            buggy.turnLeft((center_x/160)*100)
                        creep_once, moving_forward = True, False
                    else:
                        #No contours
                        print "Can't detect anything"
                    del arrow_buffer[:]
                      
            except:
                pass

            """ MOVING THE BUGGY (Don't delete!) """
        
            if (moving_forward and not wait_once) or (creep_once):
                for x in range(10):
                    wait()
                if confident_match:
                    buggy.forward(1)
                    for x in range(10):
                        wait()
                    confident_match = False
                else:
                    buggy.creep()
                if creep_once:
                    creep_once = False
                elif buggy.isStuck(mean_t=0.98, std_t=0.01):
                    print "I think I'm stuck! Randomised reverse..."
                    buggy.randomisedRecovery()
                elif turn_counter >= MAX_TURN_STEPS:
                        # Set wheel direction to neutral
                        wheel_direction = "neutral"
                        buggy.straightenWheels()
                        turn_counter = 0
                elif wheel_direction is not "neutral":
                    # Increment Turn Counter
                    turn_counter += 1
            elif wait_once:
                wait_once = False
                
            """ DISPLAYING IMAGE """
            if DISPLAY:

                # Show
                try:
                    cv2.imshow('detected_circles',display_image)
                except:
                    pass
                if DETECT_FLOOR:
                    try:
                        cv2.imshow('birds_eye',birds_eye_copy)
                    except:
                        pass
                    try:
                        cv2.imshow('Chroma_red_birds', Chroma_red)
                    except:
                        pass
                if DETECT_WALL:
                    try:
                        cv2.imshow('Chroma_red_normal', Chroma_red_normal)
                    except:
                        pass
                try:
                    cv2.imshow('cropped_image',crop_img_rgb)
                except:
                    pass
                try:
                    cv2.imshow('best_match',arrow_list[best_arrow])
                except:
                    pass
                
                
                k = cv2.waitKey(33)
                if k==27:    # Esc key to stop
                    cv2.destroyAllWindows()
                    break
            
            # Wait
            wait()

    except KeyboardInterrupt:
        print "Keyboard Interrupt Detected!"

    finally:
        # Stop the video feed
        buggy.exitBuggy()
        #exit()
