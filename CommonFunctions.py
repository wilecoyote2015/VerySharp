# -*- coding: utf-8 -*-
"""
    This file is part of verysharp,
    copyright (c) 2016 Björn Sonnenschein.

    verysharp is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    verysharp is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with verysharp.  If not, see <http://www.gnu.org/licenses/>.
"""

import cv2
import numpy as np

## Convert the Image, whih is given as numpy array, into OpenCV compatible
#  format and upscale it.
#  @param image data of astropy hdu containing the image
#  @return upscaled Image in Opencv compatible Numpy format.
def preprocessImage(image, scale_factor, data_type=np.float32, interpolation=cv2.INTER_CUBIC):
    # convert to float32, which is much appreciated by OpenCV
    image = image.astype(data_type)        
    
    # Upscale the Image
    image_upscaled = cv2.resize(image,
                 None,
                 fx=scale_factor,
                 fy=scale_factor,
                 interpolation=interpolation)
                 
    return image_upscaled