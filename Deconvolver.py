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
import cv2

## Applies Richardson-Lucy Deconvolution to an image
# @todo: for some reason, intensity decays!
# @todo: as psf, use calculated one, which should be a box kernel convolved
# with a gaussian kernel and also with respect to the upscaling algorithm.
class Deconvolver:
    ## The constructor
    #  @param config the config file object
    def __init__(self):
        self.sigma = 1.1
        self.iterations = 40
        self.kernel_size = 7
        self.scale_factor = np.sqrt(2.)
        
    ## Apply Richardson-Lucy deconvolution to the Image
    #  @param image input image as numpy array
    #  @return deconvolved image as numpy array
    def deconvolveLucy(self, image, continue_processing=None, signal_status_update=None):
        # create the kernel
        kernel = self.calculateKernel()

        # flip the kernel for the convolution
        kernel_flipped_vertically = np.flipud(kernel)
        kernel_flipped = np.fliplr(kernel_flipped_vertically)

        # set input image as initial guess
        recent_reconstruction = np.copy(image)
        
        # recursively calculate the maximum likelihood solution
        for i in range(self.iterations):
            if continue_processing is not None and continue_processing[0] == False:
                return "aborted"
                
                
            percentage_finished = round(100. * float(i) / float(self.iterations))
            status = "deconvolving: " + str(percentage_finished) + "%"
            if signal_status_update is not None:
                signal_status_update.emit(status)
            
            # convolve the recent reconstruction with the kernel
            convolved_recent_reconstruction = cv2.filter2D(recent_reconstruction,
                                                           -1,
                                                           kernel_flipped)
            
            # calculate the correction array
            correction = image / convolved_recent_reconstruction
            
            # get infinite values (from divisions by zero)
            infinite_values = np.invert(np.isfinite(correction))
            
            #set infinite values to zero because according pixels are black
            correction[infinite_values] = 0.

            # convolve the correction
            convolved_correction = cv2.filter2D(correction,
                                                -1,
                                                kernel)

            recent_reconstruction *= convolved_correction

        # print(recent_reconstruction)

        return recent_reconstruction
        
            
    ## create a kernel image with a psf
    #  @todo: enable passing of psf
    #  @return kernel as numpy array
    def calculateKernel(self):
        kernel = np.zeros([self.kernel_size, self.kernel_size])
        
        # float because this "index" is only used for calculations
        center_index = (float(self.kernel_size) - 1.) / 2.
        
        # iterate through the whole kernel and fill the pixels with psf values
        for x in range(self.kernel_size):
            for y in range(self.kernel_size):
                pixel_value = self.calculatePSF(x, y, center_index)
                kernel[x][y] = pixel_value
                
        # normalize the kernel
        kernel /= np.sum(kernel)

        return kernel
    
    # # gauss PSF for testing
    # def calculatePSF(self, x, y, center_index):
    #     quad_distance = (x - center_index)**2 + (y - center_index)**2
    #     output_value = 1. / (2.*np.pi*pow(self.sigma,2)) * np.exp( - quad_distance / (2. * pow(self.sigma,2)))
    #     return output_value

    def calculatePSF(self, x, y, center_index):
        distance = np.sqrt((x - center_index) ** 2 + (y - center_index) ** 2)
        pixel_size = self.scale_factor
        pixel_radius = pixel_size / 2.

        X = np.minimum(pixel_size, distance + pixel_radius)
        Y = np.minimum(np.maximum(0., distance - pixel_radius), pixel_size)
        Z = np.maximum(0., pixel_radius - distance)
        result = X - Y + Z + (- X**2 + Y**2 - Z**2) / (2. * pixel_size)

        return result

if __name__ == "__main__":
    input_directory = "/run/media/bjoern/daten/Programming/Test_VerySharp/crop_draussen_1/bilder/"
    input_file = "out_2_cubic.png"
    output_file = "deconvolved_25.png"
    kernel_output_file = "kernel_25.png"

    from os.path import join
    input_filepath = join(input_directory, input_file)
    output_filepath = join(input_directory, output_file)
    kernel_filepath = join(input_directory, kernel_output_file)


    image = cv2.imread(input_filepath).astype(np.float32)
    deconvolver = Deconvolver()
    result = deconvolver.deconvolveLucy(image)

    cv2.imwrite(output_filepath, result)
    kernel = deconvolver.calculateKernel()
    kernel_max = 255 / np.amax(kernel)
    kernel_brightened = kernel * kernel_max
    cv2.imwrite(kernel_filepath, kernel_brightened)