# -*- coding: utf-8 -*-
"""
Created on Wed Sep 21 20:10:24 2016

@author: wile
"""

""" 
TODO: In order to work with memory critical amounts of images,
the program has to be restructured:
- the images are stored in a two-dimensional array, holding triples of images 
(as hdulists), transformation matrices and maps for distortion correction.
- IMPORTANT: Scaling has to be done in each step individually then!
- in fitsstacker:
- at first, the array is passed to a function of aligner, 
calculating transformation matrices for each image.
- Then, the array is passed to a function of the undistorter, which calculates
the undistortion maps, by first transforming each image in a local variable
with the alignment matrix and then calculating optical flows. Do that for each
image in order to save memory. local variables are used for the images because
astropy does not use ram for the fits (if set so in the load fits function?),
so that loading all images into ram is not necessary.
- then, all images are aligned using transformation with the matrix, 
undistorted using the remap function and then stacked one by one. 
- It should be configurable via config whether alignment and undistortion is
performed. Use if conditions here for that!
"""

import numpy as np
import ImageAligner
import cv2
import ImageDataHolder
import CommonFunctions
import Deconvolver


class ImageStacker:
    def __init__(self):       
        self.scale_factor = 1.4
    
    ## stack a set of Images by averaging
    #  @param images list of astropy fits Objects 
    def stackImages(self, image_paths):
        
        # build the image data object containing the hdulists
        dataset = ImageDataHolder.ImageDataHolder(image_paths)     
        
        # create output image as numpy array with upscaled image size
        image_dimension = cv2.imread(image_paths[0]).data.shape
        stacked_image = np.zeros(image_dimension, np.float32)
        stacked_image_upscaled = cv2.resize(stacked_image,
                                            None,
                                            fx=self.scale_factor,
                                            fy=self.scale_factor,
                                            interpolation=cv2.INTER_CUBIC)
        
        # instanciate the image aligner object
        image_aligner = ImageAligner.ImageAligner(self.scale_factor)
        
        # calculate the transformation matrices for alignment
        image_aligner.calculateTransformationMatrices(dataset)
            
# will be used for motion detection in the far future...
#        # calculate distortion maps
#        if self.config["Processing_Options"]["correct_seeing"] == "True":
#            # instanciate the flow calculator object
#            flow_calculator = FlowCalculator.FlowCalculator(self.config, self.scale_factor)
#            
#            # calculate the distortion maps
#            flow_calculator.calculateDistortionMaps(dataset)
            
        # average images; iterate through all images
        num_images = len(image_paths) # number of images = length of image list
        for index in range(num_images):
            
            print ("stacking image ", index)

            # get the data of given index
            data = dataset.getData(index)
            
            # align and undistort image
            image_processed = self.processImage(index, data)
            
            # stack the image
            stacked_image_upscaled += image_processed
            
        stacked_image_upscaled /= num_images

        print ("deconvolve image")
        deconvolver = Deconvolver.Deconvolver()
        stacked_image_upscaled_deconvolved = deconvolver.deconvolveLucy(stacked_image_upscaled)
        
        return stacked_image_upscaled_deconvolved
    
    
    ## align and undistort the image.
    #  @param data dictionary of {hdu_list, transform_matrix, distortion_map}
    #  @return processed image as numpy float32 array
    def processImage(self, index, data):
        # get the image
        image = CommonFunctions.preprocessHduImage(data["image"], 
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
