# -*- coding: utf-8 -*-
"""
Created on Wed Sep 21 22:46:19 2016

@author: wile
"""

import cv2
import os

class FileHandler:
    def __init__(self):
        pass
    
    ## load all FITS files in the given directory
    #  @param path_directory path to the directory as string
    #  @return list containing the loaded fits datasets
    def loadAllFilesInDirectory(self, path_directory):
        image_paths = []
        
        # iterate through all files in the directory, try to open them
        # in order to check if they are valid files and add their data to
        # the list on success
        for filename in os.listdir(path_directory):
            file_path = os.path.join(path_directory, filename)
            
            print ("loading image ", file_path)
            
            try:
                cv2.imread(file_path)  # check if this is an image by trying to load it.
                image_paths.append(file_path)
            except:
                pass # do nothing in this iteration on failure
        return image_paths