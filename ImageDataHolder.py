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
            self.transform_matrices.append([])
            self.distortion_maps.append([])

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

    def appendTransformMatrix(self, index, transform_matrix):
        self.transform_matrices[index].append(transform_matrix)
        
    def setDistortionMap(self, index, distortion_map):
        self.distortion_maps[index] = distortion_map
        
        # @todo: function to get image count