# A generic template for a buggy module

# ******************** MODULE *********************
#
# Author: 
# Date: 
#
# Description: 
#   
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

        while True:
            
            # Get current Image
            current_image = buggy.getCurrentImage()
            while current_image is None:
                current_image = buggy.getCurrentImage()

            # Do something with it
            
            """ DISPLAYING IMAGE """
            if DISPLAY:

                cv2.imshow('normal',current_image)
                
                k = cv2.waitKey(33)
                if k==27:    # Esc key to stop
                    cv2.destroyAllWindows()
                    break
            
            # Wait
            wait()

    finally:
        # Stop the video feed
        buggy.exitBuggy()
        #exit()
