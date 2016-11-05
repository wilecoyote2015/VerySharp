# -*- coding: utf-8 -*-
"""
Created on Wed Sep 28 10:21:49 2016

@author: wile
"""

import cv2
import numpy as np

## Convert the Image, whih is given as numpy array, into OpenCV compatible
#  format and upscale it.
#  @param image data of astropy hdu containing the image
#  @return upscaled Image in Opencv compatible Numpy format.
def preprocessHduImage(image, scale_factor):
    # convert to float32, which is much appreciated by OpenCV
    image_float32 = image.astype(np.float32)        
    
    # Upscale the Image
    image_upscaled = cv2.resize(image_float32,
                 None,
                 fx=scale_factor,
                 fy=scale_factor,
                 interpolation=cv2.INTER_CUBIC)                     
                 
    return image_upscaled