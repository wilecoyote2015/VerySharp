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
        self.scale_factor = 2.
        self.continue_processing = [True]  # wrapper for passing per reference
        self.tile_size = 1024
        self.tile_margin = 256
        self.tiles = None
        self.bool_deconvolve = True

        self.interpolation_upscale = cv2.INTER_CUBIC
        
        
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
        
        # instanciate the image aligner object
        image_aligner = ImageAligner.ImageAligner(self.scale_factor)
        
        # calculate the transformation matrices for alignment
        image_dimension = cv2.imread(self.image_paths[0]).shape
        self.tiles = self.calculateTiles(image_dimension)
        image_aligner.calculateTransformationMatrices(dataset, 
                                                      self.tiles,
                                                      self.continue_processing,
                                                      self.signal_status_update)
        
        # create output image as numpy array with upscaled image size
        stacked_image = np.zeros(image_dimension, np.float32)
        stacked_image_upscaled = cv2.resize(stacked_image,
                                            None,
                                            fx=self.scale_factor,
                                            fy=self.scale_factor,
                                            interpolation=cv2.INTER_CUBIC)
            
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
            
            del data
            
            # stack the image
            stacked_image_upscaled += image_processed

        stacked_image_upscaled /= num_images

        print ("deconvolve image")
        if self.continue_processing[0]:
            if self.bool_deconvolve:
                deconvolver = Deconvolver.Deconvolver()
                stacked_image_upscaled_deconvolved = deconvolver.deconvolveLucy(stacked_image_upscaled,
                                                                                self.continue_processing,
                                                                                self.signal_status_update)
            else:
                stacked_image_upscaled_deconvolved = stacked_image_upscaled
        #stacked_image_upscaled_deconvolved = stacked_image_upscaled

        if self.continue_processing[0]:
            cv2.imwrite(self.output_path, stacked_image_upscaled_deconvolved)
            self.signal_status_update.emit("finished!")
    
        self.signal_finished.emit()

    ## align and undistort the image.
    #  @param data dictionary of {hdu_list, transform_matrix, distortion_map}
    #  @return processed image as numpy float32 array
    def processImage(self, index, data):
        # get the image
        raw_image = CommonFunctions.preprocessImage(data["image"], 
                                                   self.scale_factor,
                                                    interpolation=self.interpolation_upscale)
        image_dimension = raw_image.shape

        # create output image as numpy array with upscaled image size
        processed_image = np.zeros(image_dimension, np.float32)
        
        # align all tiles
        for tile, transform_matrix in zip(self.tiles, data["transform_matrix"]):

            tile_slice_raw_image = np.s_[tile["y"][0]:tile["y"][1],
                                         tile["x"][0]:tile["x"][1]]
            raw_image_tile = raw_image[tile_slice_raw_image]
            tile_aligned = cv2.warpAffine(raw_image_tile,
                                          transform_matrix,
                                          (raw_image_tile.shape[1],raw_image_tile.shape[0]),
                                          flags=cv2.INTER_CUBIC + cv2.WARP_INVERSE_MAP);      
                                          
            # Insert the inner area of tile_aligned (so without margins) into
            # the appropriate area in the processed image
            min_x = tile["x"][0] + tile["margin_x"][0]
            min_y = tile["y"][0] + tile["margin_y"][0]
            max_x = tile["x"][1] - tile["margin_x"][1]
            max_y = tile["y"][1] - tile["margin_y"][1]
            tile_slice_processed_image = np.s_[min_y:max_y,
                                               min_x:max_x]
                                               
            max_y_aligned = tile_aligned.shape[0] - tile["margin_y"][1]
            max_x_aligned = tile_aligned.shape[1] - tile["margin_x"][1]
            tile_aligned_slice = np.s_[tile["margin_y"][0]:max_y_aligned,
                                       tile["margin_x"][0]:max_x_aligned]                                
                                               
            tile_aligned_without_margin = tile_aligned[tile_aligned_slice]
                                          
            processed_image[tile_slice_processed_image] = tile_aligned_without_margin
                                       
        return processed_image

    def calculateTiles(self, image_dimension):
        # todo: also save the effective margins in some way for later processing
        image_dimension_upscaled = (np.round(np.multiply(image_dimension,self.scale_factor))).astype(int)  # TODO: correct rounding?
        
        tiles = []
        
        num_tiles_x = int(np.ceil(image_dimension_upscaled[1] / self.tile_size))
        num_tiles_y = int(np.ceil(image_dimension_upscaled[0] / self.tile_size))
        
        # attention: max values are indices for slicing, so they are in fact
        # max + 1 due to python indexing!
        for index_y in range(num_tiles_y):
            for index_x in range(num_tiles_x):
                
                min_x_without_margins = index_x * self.tile_size
                min_y_without_margins = index_y * self.tile_size
                max_x_without_margins = (index_x + 1) * self.tile_size
                max_y_without_margins = (index_y + 1) * self.tile_size

                min_x = min_x_without_margins - self.tile_margin
                min_y = min_y_without_margins - self.tile_margin
                max_x = max_x_without_margins + self.tile_margin
                max_y = max_y_without_margins + self.tile_margin
                
                # correct for image bounds
                min_x_corrected = max(min_x, 0)
                min_y_corrected = max(min_y, 0)
                max_x_corrected = min(max_x, image_dimension_upscaled[1])
                max_y_corrected = min(max_y, image_dimension_upscaled[0])
                
                # calculate effective margins
                min_x_without_margins = max(min_x_without_margins, 0)
                min_y_without_margins = max(min_y_without_margins, 0)
                max_x_without_margins = min(max_x_without_margins, image_dimension_upscaled[1])
                max_y_without_margins = min(max_y_without_margins, image_dimension_upscaled[0])
                margin_x_left = min_x_without_margins - min_x_corrected
                margin_y_left = min_y_without_margins - min_y_corrected
                margin_x_right = max_x_corrected - max_x_without_margins
                margin_y_right = max_y_corrected - max_y_without_margins
                
                tile = {"x":[min_x_corrected,max_x_corrected],
                        "y":[min_y_corrected,max_y_corrected],
                        "margin_x":[margin_x_left,margin_x_right],
                        "margin_y":[margin_y_left,margin_y_right]}
                tiles.append(tile)
                
        return tiles
                
                