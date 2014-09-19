# Copyright (c) 2014
# Joey Green, School of Engineering and Computer Sciences, Durham University, UK

# All versions of this software (both binary and source) must retain
# and display this copyright notice.

# License : GPL - http://www.gnu.org/copyleft/gpl.html

# ******************** RANDOM SEARCH MODULE *********************
#
# Author: Joey Green
# Date: 05/09/14
#
# Description: This module uses the Buggy module, and allows the Buggy to
#   randomly search for a provided image
#
# ***************************************************************

import cv2
import cv2.cv as cv
import time
import numpy as np
from matplotlib import pyplot as plt
from buggy import Buggy
import sys

# ********************** VARIABLES **********************
#
# Modify these to tailor to your environment.
#

DISPLAY = True # Whether you want to display what the Buggy sees

# The path to the image which the buggy will look for, e.g. 'C:\\Users\\User\\Images\\Goal_Image.png'
PATH_GOAL_IMAGE = 'C:\\Users\\Joey\\Documents\\Work\\Year_3\\Internship\\Template_Matching\\Photoshop\\Old\\Up_old.png'

GOAL_THRESHOLD = 0.7 # The threshold to use when matching the goal image - lower it is, the easier to find, but easier to make mistakes

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
            cv2.namedWindow('normal',cv2.WINDOW_NORMAL)
            cv2.namedWindow('goal',cv2.WINDOW_NORMAL)

        # Set found to false
        found_goal = False

        # Get the current Image for reference (don't save it)
        current_image = buggy.getCurrentImage(append=False)
        while current_image is None:
            current_image = buggy.getCurrentImage(append=False)

        # Set goal image
        goal_image = cv2.imread(PATH_GOAL_IMAGE)
        # Resize so smaller than video dimensions - keep halving till smaller
        while goal_image.shape[0] > current_image.shape[0] or goal_image.shape[1] > current_image.shape[1]:
            goal_image = cv2.resize(goal_image, (goal_image.shape[0]/2, goal_image.shape[1]/2))
        _, goal_w, goal_h = goal_image.shape[::-1]

        # Loop while still searching
        while not found_goal:
            
            # Get current Image
            current_image = buggy.getCurrentImage()
            while current_image is None:
                current_image = buggy.getCurrentImage()

            # Match goal to camera image
            res_goal = cv2.matchTemplate(current_image,goal_image,cv2.TM_CCOEFF_NORMED)
            best_match = np.amax(res_goal)

            # If found a match above threshold,
            if best_match > GOAL_THRESHOLD:

                # Draw on Current Image
                goal_loc = np.where( res_goal >= GOAL_THRESHOLD)
                for pt in zip(*goal_loc[::-1]):
                    cv2.rectangle(current_image, pt, (pt[0] + goal_w, pt[1] + goal_h), (0,0,255), 2)

                print 'Found with', best_match, 'match!' # Print result
                found_goal = True # Stop
            else:
                # Move forward
                buggy.creep()
                # If stuck, randomly reverse
                if buggy.isStuck(mean_t=0.98, std_t=0.01):
                    print "I think I'm stuck! Randomised reverse..."
                    buggy.randomisedRecovery()
            
            """ DISPLAYING IMAGE """
            if DISPLAY:

                cv2.imshow('normal',current_image)
                cv2.imshow('goal',goal_image)
                
                k = cv2.waitKey(33)
                if k==27:    # Esc key to stop
                    cv2.destroyAllWindows()
                    break
            
            # Wait
            wait()

        # Wait for key press and end
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    finally:
        # Stop the video feed
        buggy.exitBuggy()
        #exit()
