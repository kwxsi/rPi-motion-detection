import cv2	# importing openCV here
import sys
import random
import numpy as np	# importing Numpy for calculations


class Detector():
	def __init__(self, image_name):
		self.image_name = image_name	# The image file name
		self.image = []			# OpenCV image array
		self.drawn = 0			# Count of how many detector-boxes have been drawn
		self.drawColors = [(255,0,0),(0,255,0),(0,0,255),(255,255,0),(255,0,255),(0,255,255)] #RGB Values
		# self.path  = "/home/pi/CV/opencv-3.1.0/data/haarcascades/"
		self.path = "xml/"		# The path to the haarcascades data xml files
		self.rects = []			# Discovered rectangles from Image Analysis

	def detect(self, xml):			# Detect people in image and save the image bounds around them
		cascade = cv2.CascadeClassifier(self.path + xml)
		self.image = cv2.imread(self.image_name)  # Loads the image into a numpy array
		gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
		hits = cascade.detectMultiScale(	  # Grayscale and analyze image using 
			gray,				  #  the selected cascade classifier file
			scaleFactor=1.1,
			minNeighbors=5,
			minSize=(10, 10),
			flags=cv2.CASCADE_SCALE_IMAGE
		)
		self.rects.append(hits)		# Add detected people to rect-list for drawing
		return hits			# Can use len(hits) to check if anyone was found

	# The following functions provide an xml file to be used as the cascade classifier
	#  to detect different things, such as face, upper body, or pedestrian
	def face(self):
		return self.detect('haarcascade_frontalface_default.xml')

	def face2(self):
		return self.detect('haarcascade_frontalface_alt.xml')

	def face3(self):
		return self.detect('haarcascade_frontalface_alt2.xml')

	def full_body(self):
		return self.detect('haarcascade_fullbody.xml')

	def upper_body(self):
		return self.detect('haarcascade_upperbody.xml')

	def lower_body(self):
                return self.detect('haarcascade_lowerbody.xml')

	#def pedestrian(self):
		#return self.detect('hogcascade_pedestrians.xml')

	# This function will draw the rectangles around all objects found and then 
	#  overwrite the original image file.
	def draw(self):
		for hits in self.rects:
			color = self.drawColors[self.drawn % len(self.drawColors)] # Rect color selection
			self.drawn += 1
			for (x,y,w,h) in hits:
				cv2.rectangle(self.image, (x, y), (x+w, y+h), color, 1) # Draws the Rect
		cv2.imwrite(self.image_name, self.image)	# Saves the file over the original image name
		return hits

