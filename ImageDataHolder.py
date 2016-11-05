# -*- coding: utf-8 -*-
"""
Created on Wed Sep 28 09:16:14 2016

@author: wile
"""

import cv2

class ImageDataHolder:
    ## The Constructor
    #  @param hdu_lists List of astropy hdulist objects containing images from fits.
    def __init__(self, image_paths):
        self.image_paths = image_paths
        self.transform_matrices = []
        self.distortion_maps = []
        
        # Fill the other lists with None so that they have the right length
        num_images = len(image_paths)
        for index in range(num_images):
            self.transform_matrices.append(None)
            self.distortion_maps.append(None)

    ## Get data at given index
    #  @param index integer index of the data to get
    #  @return dictionary of {hdu_list, transform_matrix, distortion_map}
    def getData(self, index):
        return {"image" : cv2.imread(self.image_paths[index]),
                "transform_matrix" : self.transform_matrices[index],
                "distortion_map" : self.distortion_maps[index]}
    
    def getImageSize(self, index):
        return cv2.imread(self.image_paths[index].shape)
                          
    def getImageCount(self):
        return len(self.image_paths)

    def setTransformMatrix(self, index, transform_matrix):
        self.transform_matrices[index] = transform_matrix
        
    def setDistortionMap(self, index, distortion_map):
        self.distortion_maps[index] = distortion_map
        
        # @todo: function to get image count