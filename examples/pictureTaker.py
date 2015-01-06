# Copyright (c) 2014
# Joey Green, School of Engineering and Computer Sciences, Durham University, UK

# All versions of this software (both binary and source) must retain
# and display this copyright notice.

# License : GPL - http://www.gnu.org/copyleft/gpl.html

# ******************** PICTURE TAKER MODULE *********************
#
# Author: Joey Green
# Date: 05/09/14
#
# Description: This module uses the Buggy module, and allows the Buggy to
#   take pictures and save them at a desired file location
#
# ***************************************************************

import sys
import cv2
import cv2.cv as cv
import time
import numpy as np
from matplotlib import pyplot as plt
sys.path.append('../sdk')
from buggy import Buggy

# ********************** VARIABLES **********************
#
# Modify these to tailor to your environment.
#

DISPLAY = True # Whether you want to display what the Buggy sees

IMAGES_TO_SAVE = 5 # How many images to save

# Location to save images. E.g. '\\Users\\ImageDump\\Directory\\'
SAVE_LOCATION = '..\\doc\\dump\\'

WAIT_INTERVALS = 0.5 # Interval to wait (in seconds) between each picture taken

# *******************************************************

# ******************** LOCAL FUNCTIONS ******************

def wait():
    time.sleep(WAIT_INTERVALS)

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

        while IMAGES_TO_SAVE > 0:
            
            # Get current Image
            current_image = buggy.getCurrentImage()
            while current_image is None:
                current_image = buggy.getCurrentImage()

            # Save it
            u_string = str(time.clock()).replace(".","")
            cv2.imwrite(SAVE_LOCATION + u_string + '.png', current_image)
            IMAGES_TO_SAVE -= 1
            
            """ DISPLAYING IMAGE """
            if DISPLAY:

                cv2.imshow('normal',current_image)
                
                k = cv2.waitKey(33)
                if k==27:    # Esc key to stop
                    cv2.destroyAllWindows()
                    break
            
            # Wait
            wait()

        # Destroy window
        cv2.destroyAllWindows()

    finally:
        # Stop the video feed
        buggy.exitBuggy()
        #exit()
