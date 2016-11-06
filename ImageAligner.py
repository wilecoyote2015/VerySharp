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
import CommonFunctions

class ImageAligner:
    
    ## The constructor
    #  @param reference_image the reference Image as float numpy array
    def __init__(self, scale_factor):
        self.scale_factor = scale_factor
        self.motion_type = cv2.MOTION_AFFINE
        
    ## Calculate the Transformation matrices for all images in the dataset
    #  @param dataset ImageDataHolder object with filled hdulists and empty 
    #  transform matrices
    #  @return dataset with filled tansform_matrices for upscaled images
    def calculateTransformationMatrices(self, dataset, continue_processing, signal_status_update):
        # fill unity matrix for first image
        unity_transform_matrix = np.eye(2, 3, dtype=np.float32)
        dataset.setTransformMatrix(0, unity_transform_matrix)  #@todo: is this possible inplace?
        
        # set the first image as reference
        first_data = dataset.getData(0)
        image_reference = CommonFunctions.preprocessImage(first_data["image"], 
                                                             self.scale_factor)
    
        # iterate through the dataset and create the tansformation matrix for each.
        # except the first one
        num_images = dataset.getImageCount()
        for index in range(1, num_images):
            
            if continue_processing[0] == False:
                return "aborted"
            
            print ("calculating transformation map for alignment of image ", index)      
            
            status = "aligning image " + str(index + 1) + " of " + str(num_images)
            signal_status_update.emit(status)
            
            # Get the image at the index
            data = dataset.getData(index)
            image = CommonFunctions.preprocessImage(data["image"], 
                                                       self.scale_factor)
            
            # rough inital alignment using feature detection
            refercence_image_8u = cv2.cvtColor(image_reference, cv2.COLOR_BGR2GRAY).astype(np.uint8)
            image_8u = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.uint8)
            warp_matrix = cv2.estimateRigidTransform(refercence_image_8u, image_8u, False)
            
            # if estimateRigidTransform has failed, create unity matrix
            if warp_matrix is None:
                print ("WARNING: Initial alignment for Image ", index, " failed!")
                warp_matrix = np.eye(2,3, dtype=np.float32)
            
            # convert warp matrix to float32 because findTransformECC needs this            
            warp_matrix = warp_matrix.astype(np.float32)   
            
            # @todo: those two parameters can be set in config!
            # Specify the number of iterations for ECC alignment.
            number_of_iterations = 5000;
             
            # Specify the threshold of the increment
            # in the correlation coefficient between two iterations
            termination_eps = 1e-5;
            
            # Define termination criteria
            criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
                        number_of_iterations,  termination_eps)
             
            # Run the ECC algorithm. The results are stored in warp_matrix.
            (cc, transform_matrix) = cv2.findTransformECC(refercence_image_8u,
                                                          image_8u, 
                                                          warp_matrix, 
                                                          self.motion_type, 
                                                          criteria)
            
            # fill the warp matrix into the dataset
            dataset.setTransformMatrix(index, transform_matrix)
            
        return dataset