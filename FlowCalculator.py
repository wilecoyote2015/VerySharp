# -*- coding: utf-8 -*-
"""
Created on Thu Sep 29 10:30:06 2016

@author: wile
"""

import CommonFunctions
import cv2
import numpy as np
import os

## Provides a Method to calculate OpenCV maps for a series of images
#  that can be used to correct seeing distortion with the OpenCV remap function
class FlowCalculator:
    def __init__(self, config, scale_factor):
        self.config = config

        self.extension = int(config["FITS_Options"]["extension"])
        self.scale_factor = scale_factor        
        
        self.optical_flow_output_directory = config["Filepaths"]["monitoring_images_output_directory"]
        
        self.pyr_scale = float(config["Optical_Flow_Options"]["pyr_scale"])
        self.levels = int(config["Optical_Flow_Options"]["levels"])
        self.winsize = int(config["Optical_Flow_Options"]["winsize"])
        self.iterations = int(config["Optical_Flow_Options"]["iterations"])
        self.poly_n = int(config["Optical_Flow_Options"]["poly_n"])
        self.poly_sigma = float(config["Optical_Flow_Options"]["poly_sigma"])
        
    
    ## calculate a Distortion map based on optical flow
    #  @param dataset ImageDataHolder object with filled hdulists, filled
    #  transform matrices and empty distortion maps
    #  @return dataset with filled tansform_matrices for upscaled images
    #  @todo: do not calculate distortion relative to reference image, 
    #  but as average!
    def calculateDistortionMaps(self, dataset):
        # set the first image as reference
        first_data = dataset.getData(0)
        first_hdu_image = first_data["hdu_list"][self.extension].data
        image_reference = CommonFunctions.preprocessHduImage(first_hdu_image, 
                                                             self.scale_factor)
    
        # @todo: for case that alignment is not relative to first image, also
        # do alignment transformation for first image!
    
        # calculate the optical flows for each image
        list_optical_flows = self.calculateOpticalFlowsForDataset(image_reference,
                                                                  dataset)
                                                  
        # calculate the mean optical flow in order to correct the seeing
        # not relative to the reference image, but relative to the
        # average shape which should approximate the real object better.
        optical_flow_mean =  self.calculateMeanOpticalFlow(list_optical_flows)                                               
                     
        # calculate the distortion maps from optical flows for each image
        num_optical_flows = len(list_optical_flows)           
        for index in range(num_optical_flows):   
            
            optical_flow = list_optical_flows[index]
            
            # subtract mean optical flow
            optical_flow -= optical_flow_mean
                 
            # create the distortion map from the optical flow vectorfield
            distortion_map = self.convertOpticalFlowToDistortionMap(optical_flow)

            # set the distortion map in the dataset for this image 
            dataset.setDistortionMap(index, distortion_map)

        return dataset


    ## Calculates optical flows for a set of images relative to first image
    #  @param image_reference reference image as numpy float32 array
    #  @param dataset ImageDataHolder object with filled hdulists, filled
    #  transform matrices and empty distortion maps
    #  @return list object containing optical flows as numpy array
    def calculateOpticalFlowsForDataset(self, image_reference, dataset):
        # optical flows will be stored here        
        list_optical_flows = []
        
        # add zero optical flow for the reference image which is at first position
        shape_image_reference = image_reference.shape
        shape_optical_flow = [shape_image_reference[0],
                              shape_image_reference[1],
                              2] 
        zero_optical_flow = np.zeros(shape_optical_flow, np.float32)
        list_optical_flows.append(zero_optical_flow)
        
        # iterate through the dataset and calculate the optical flow for each
        # except the first one
        num_images = dataset.getImageCount()
        for index in range(1, num_images):
            
            print ("calculating optical flow for image ", index)      
            
            # Get the image at the index
            data = dataset.getData(index)
            hdu_image = data["hdu_list"][self.extension].data
            image = CommonFunctions.preprocessHduImage(hdu_image, 
                                                       self.scale_factor)
            
            # @todo: here, do not use config but simply check if matrix is None
            # apply the transformation to the input image
            if self.config["Processing_Options"]["align_images"] == "True":
                # get the image dimension
                image_shape = image.shape
                
                # Transform the Image
                image = cv2.warpAffine(image,
                                       data["transform_matrix"],
                                       (image_shape[1],image_shape[0]),
                                       flags=cv2.INTER_CUBIC + cv2.WARP_INVERSE_MAP)       
            
            # calculate the optical flow (backwards for warping!)
            optical_flow = cv2.calcOpticalFlowFarneback(image_reference,
                                                        image,
                                                        None,
                                                        self.pyr_scale,
                                                        self.levels,
                                                        self.winsize,
                                                        self.iterations,
                                                        self.poly_n,
                                                        self.poly_sigma,
                                                        cv2.OPTFLOW_FARNEBACK_GAUSSIAN)

            # Write out optical flow images for user evaluation
            self.writeOpticalFlowImage(index, optical_flow)

            list_optical_flows.append(optical_flow)
            
        return list_optical_flows

    
    ## Average a list of optical flows
    #  @param list_optical_flows list object containing optical flows as numpy arrays
    #  @return averaged optical flow as numpy array
    def calculateMeanOpticalFlow(self, list_optical_flows):
        # create zero optical flow where other flows will be added and averaged
        optical_flow_mean = np.zeros_like(list_optical_flows[0])  
        
        # average all optical flows in list
        num_optical_flows = len(list_optical_flows)
        for optical_flow in list_optical_flows:
            optical_flow_mean += optical_flow / float(num_optical_flows)
            
        return optical_flow_mean


    ## Calculate an OpenCV map that can be used to remap an image according
    #  to the optical flow vector field using OpenCV remap function
    #  @param optical_flow optical flow as numpy array
    #  @param distortion_map OpenCV map as numpy array
    def convertOpticalFlowToDistortionMap(self, optical_flow):
        # get x and y resolution of optical flow (and so also of image)    
        shape_optical_flow = optical_flow.shape[:-1]
        
        # create empty distortion maps for x and y separately because 
        # opencv remap needs this
        distortion_map_x = np.zeros(shape_optical_flow, np.float32) # only x and y
        distortion_map_y = np.zeros(shape_optical_flow, np.float32) # only x and y 
        
        # fill the distortion maps
        for x in range(shape_optical_flow[1]):
            distortion_map_x[:,x] = optical_flow[:,x,0] + x
        for y in range(shape_optical_flow[0]):
            distortion_map_y[y] = optical_flow[y,:,1] + y
                
        distortion_map = [distortion_map_x, distortion_map_y]                
                
        return distortion_map

    ## Create a colorful representation of the optical flow, where intensity
    #  denotes vector length and huw denotes vector direction
    def writeOpticalFlowImage(self, index, optical_flow):
        filename = "flow_" + str(index) + ".png"
        output_path = os.path.join(self.optical_flow_output_directory, filename)

        # create hsv image
        shape_optical_flow = optical_flow.shape[:-1]
        shape_hsv = [shape_optical_flow[0], shape_optical_flow[1], 3]
        hsv = np.zeros(shape_hsv, np.float32)
        
        # set saturation to 255
        hsv[:,:,1] = 255
        
        # create colorful illustration of optical flow
        mag, ang = cv2.cartToPolar(optical_flow[:,:,0], optical_flow[:,:,1])
        hsv[:,:,0] = ang*180/np.pi/2
        hsv[:,:,2] = cv2.normalize(mag,None,0,255,cv2.NORM_MINMAX)
        bgr = cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)

        cv2.imwrite(output_path, bgr)