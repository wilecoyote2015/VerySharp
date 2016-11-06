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

import numpy as np
import ImageAligner
import cv2
import ImageDataHolder
import CommonFunctions
import Deconvolver
from PyQt5.QtCore import QThread, pyqtSignal


class ImageStacker(QThread):
    signal_finished = pyqtSignal()
    signal_status_update = pyqtSignal(str)
    
    def __init__(self, image_paths, output_path):       
        QThread.__init__(self)
        self.image_paths = image_paths
        self.output_path = output_path
        self.scale_factor = 1.4
        self.continue_processing = [True]  # wrapper for passing per reference
        
        
    def __del__(self):
        self.wait()
        
    def run(self):
        self.stackImages()
        
    def abort(self):
        self.continue_processing[0] = False
    
    ## stack a set of Images by averaging
    #  @param images list of astropy fits Objects 
    def stackImages(self):
        
        # build the image data object containing the hdulists
        dataset = ImageDataHolder.ImageDataHolder(self.image_paths)     
        
        # create output image as numpy array with upscaled image size
        image_dimension = cv2.imread(self.image_paths[0]).data.shape
        stacked_image = np.zeros(image_dimension, np.float32)
        stacked_image_upscaled = cv2.resize(stacked_image,
                                            None,
                                            fx=self.scale_factor,
                                            fy=self.scale_factor,
                                            interpolation=cv2.INTER_CUBIC)
        
        # instanciate the image aligner object
        image_aligner = ImageAligner.ImageAligner(self.scale_factor)
        
        # calculate the transformation matrices for alignment
        image_aligner.calculateTransformationMatrices(dataset, 
                                                      self.continue_processing,
                                                      self.signal_status_update)
            
# will be used for motion detection in the far future...
#        # calculate distortion maps
#        if self.config["Processing_Options"]["correct_seeing"] == "True":
#            # instanciate the flow calculator object
#            flow_calculator = FlowCalculator.FlowCalculator(self.config, self.scale_factor)
#            
#            # calculate the distortion maps
#            flow_calculator.calculateDistortionMaps(dataset)

        # average images
        num_images = len(self.image_paths) # number of images = length of image list
        for index in range(num_images):
            
            if self.continue_processing[0] == False:
                return "aborted"

            print ("stacking image ", index)
            status = "stacking image " + str(index + 1) + " of " + str(num_images)
            self.signal_status_update.emit(status)

            # get the data of given index
            data = dataset.getData(index)

            # align and undistort image
            image_processed = self.processImage(index, data)
            
            # stack the image
            stacked_image_upscaled += image_processed

        stacked_image_upscaled /= num_images

        print ("deconvolve image")
        if self.continue_processing[0]:
            deconvolver = Deconvolver.Deconvolver()
            stacked_image_upscaled_deconvolved = deconvolver.deconvolveLucy(stacked_image_upscaled, 
                                                                            self.continue_processing,
                                                                            self.signal_status_update)

        if self.continue_processing[0]:
            cv2.imwrite(self.output_path, stacked_image_upscaled_deconvolved)
            self.signal_status_update.emit("finished!")
    
        self.signal_finished.emit()

    
    ## align and undistort the image.
    #  @param data dictionary of {hdu_list, transform_matrix, distortion_map}
    #  @return processed image as numpy float32 array
    def processImage(self, index, data):
        # get the image
        image = CommonFunctions.preprocessImage(data["image"], 
                                                   self.scale_factor)

        image_processed = image

        # apply the transformation to the input image
        # get the image dimension
        image_shape = image.shape
        
        # @todo: here, do not use config but simply check if matrix is None
        # Transform the Image
        image_aligned = cv2.warpAffine(image,
                                       data["transform_matrix"],
                                       (image_shape[1],image_shape[0]),
                                       flags=cv2.INTER_CUBIC + cv2.WARP_INVERSE_MAP);

        image_processed = image_aligned                                           
                                       
        return image_processed
