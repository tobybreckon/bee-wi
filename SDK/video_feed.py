# Copyright (c) 2014
# Joey Green, School of Engineering and Computer Sciences, Durham University, UK

# All versions of this software (both binary and source) must retain
# and display this copyright notice.

# License : GPL - http://www.gnu.org/copyleft/gpl.html

# ******************** VIDEO THREAD MODULE *********************
#
# Author: Joey Green
# Date: 05/09/14
#
# Description: This module connects to the BeeWi Camera Buggy's camera and handles all of the image processing.
#
# *******************************************************

from threading import Thread
from matplotlib import pyplot as plt
from collections import deque
import socket
import sys
import cv2
import numpy as np
import time

import re

### Video Feed Thread ###

class video_thread(Thread):

    # Constructor
    def __init__(self, host='192.168.11.123', port=8080):
        #self.HOST, self.PORT = host, port
        self.HOST, self.PORT = '192.168.11.123', 8080
        self.image_buffer, self.image_buffer_length = deque(), 3
        self.sock = None
        self.stream_feed, self.display_feed = False, False
        self.corner_detection = False
        self.running = True
        Thread.__init__(self)
        print "Video Feed Initialised"

    # Open socket for communication
    def streamFeed(self, display=False):
        """Connects to the Buggy Video Feed. Use display=True to also display it"""
        if not self.stream_feed:
            # Connect
            try:
                # First, open socket (and set timeout)
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(5)
                # Connect and send generic bytes
                self.sock.connect((self.HOST, self.PORT))
                self.sock.send(bytearray([170,3,0,0,0,0,0,171]))
                self.stream_feed = True
                if display:
                    self.displayFeed()
            except socket.timeout:
                print "Error: Could not connect to Buggy"
        else:
            print "Video feed already streaming. Use 'displayFeed()' to display Feed"
            
    # Close socket
    def stopFeed(self):
        if self.display_feed:
            # Hide
            self.hideFeed()
        # Close socket
        self.sock.close()
        self.stream_feed = False

    # Stop thread on exit
    def closeThread(self):
        self.running = False

    # Running
    def run(self):
        
        try:
            # Receive images and handle accordingly
            img = bytearray()

            # Loop: only show image if set so
            while self.running:
                if self.stream_feed:
                    received = self.sock.recv(1024)
                    img.extend(received)
                    # If found the end of an image, snip it
                    if re.search(r'(\xff\xd9)', received) is not None:
                        # Return decoded image
                        decoded_image = self.handleImage(img)

                        # Add to image buffer
                        self.addToImageBuffer(decoded_image)
                        
                        # Only display if set to display
                        if self.display_feed:
                            try:
                                cv2.imshow('buggy_feed',decoded_image)
                                k = cv2.waitKey(33)
                                if k==27:    # Esc key to stop
                                    cv2.destroyAllWindows()
                                    break
                            except:
                                print "Error displaying frame"
                            finally:
                                if not self.display_feed:
                                    cv2.destroyAllWindows()
                                
                        # strip off used bytes and start again
                        img = bytearray(re.split(r'\xff\xd9', received)[1])
                    # Wait?
                else:
                    # Wait for a second
                    time.sleep(1)
        except socket.timeout:
            print "Error: Could not connect to Buggy"
        finally:
            # Close the socket
            if self.sock:
                self.sock.close()

    def displayFeed(self):
        if not self.stream_feed:
            print "Cannot display feed without it being streamed!"
        elif not self.display_feed:
            self.display_feed = True
        else:
            print "Video Feed already being displayed."

    def clearBuffer(self):
        self.image_buffer.clear()

    def hideFeed(self):
        if self.display_feed:
            cv2.destroyWindow('buggy_feed')
            self.display_feed = False
            self.image_buffer.clear()

    def handleImage(self, img):
        # Regex the bits we want
        split = re.split(r'(\xff\xd8\xff\xdb|\xff\xd9)', img)
        final_img = bytearray()
        for i in range(1,4): # 0 is the previous mess, 1 is header, 2 content, 3 tail, 4 is next image
            final_img.extend(split[i])
        # Convert to numpy array
        ndata = np.frombuffer(final_img, np.int8)
        # cv2 decode
        return cv2.imdecode(ndata, 1)

    def addToImageBuffer(self, img):
        if img is not None:
            self.image_buffer.appendleft(img)
            # If more than required, pop
            if len(self.image_buffer) > self.image_buffer_length:
                self.image_buffer.pop()

    def getImageFromBuffer(self, i):
        try:
            return self.image_buffer[i]
        except IndexError:
            #print "Error: Image buffer empty"
            return None

    def getCurrentImage(self):
        if self.stream_feed:
            return self.getImageFromBuffer(0)
        else:
            print "Video must be streaming to get current image"
            return None

    def getPreviousImage(self):
        if self.stream_feed:
            return self.getImageFromBuffer(1)
        else:
            print "Video must be streaming to get previous image"
            return None

    def getAllImageBuffer(self):
        return self.image_buffer

####################

if __name__ == '__main__':

    # Initialise Feed
    video_feed = video_thread()

    # Start Feed
    video_feed.start()

    # Wait to finish
    video_feed.join()

    # Print somthing
    print "Video Feed Stopped"
