/*
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
*/


#include "deconvolve.h"

void Deconvolve::DeconvolveLucy(Mat &recent_reconstruction, const Mat &kernel) 
{
	float min_value = 1e-2;
	
	int width = recent_reconstruction.cols;
	int height = recent_reconstruction.rows;
	
	Mat recent_reconstruction_convolved;
	Mat rawImage = recent_reconstruction.clone();
	
	// Create flipped kernel for convolution using filter2d
	Mat kernel_flipped;
	flip(kernel, kernel_flipped, -1);
	for(int i=0; i < 40; i++) {

		// Convolve the kernel with the blurred image
		recent_reconstruction_convolved = recent_reconstruction.clone();
		filter2D(recent_reconstruction,recent_reconstruction_convolved,-1,kernel_flipped);
		
		// Divide the actual Image by the blurred reconstruction
		Mat correction = Mat::zeros(recent_reconstruction_convolved.size(), CV_32FC3);
		divide(rawImage,recent_reconstruction_convolved,correction);
		
		// Set pixel values to zero where division by zero occured
		for ( int x = 0; x < width; x++) {
			for (int y = 0; y < height; y++) {
				if (recent_reconstruction_convolved.at<Vec3f>(y,x)[0] < min_value)
					correction.at<Vec3f>(y,x)[0] = 0.;
				if (recent_reconstruction_convolved.at<Vec3f>(y,x)[1] < min_value)
					correction.at<Vec3f>(y,x)[1] = 0.;
				if (recent_reconstruction_convolved.at<Vec3f>(y,x)[2] < min_value)
					correction.at<Vec3f>(y,x)[2] = 0.;
			}
		}	
		
		// Correlate the correction
		filter2D(correction,correction,-1,kernel);

		multiply(recent_reconstruction,correction,recent_reconstruction);
	};
}

void Deconvolve::DeconvolveGoldMeinel(cv::Mat& recent_reconstruction, const cv::Mat& kernel)
{
	float min_value = 1e-2;
	
	int width = recent_reconstruction.cols;
	int height = recent_reconstruction.rows;
	
	Mat recent_reconstruction_convolved;
	Mat rawImage = recent_reconstruction.clone();
	
	// Create flipped kernel for convolution using filter2d
	Mat kernel_flipped;
	flip(kernel, kernel_flipped, -1);
	for(int i=0; i < 40; i++) {

		// Convolve the kernel with the blurred image
		recent_reconstruction_convolved = recent_reconstruction.clone();
		filter2D(recent_reconstruction,recent_reconstruction_convolved,-1,kernel_flipped);
		
		// Divide the actual Image by the blurred reconstruction
		Mat correction = Mat::zeros(recent_reconstruction_convolved.size(), CV_32FC3);
		divide(rawImage,recent_reconstruction_convolved,correction);

		// Set pixel values to zero where division by zero occured
// 		for ( int x = 0; x < width; x++) {
// 			for (int y = 0; y < height; y++) {
// 				if (recent_reconstruction_convolved.at<Vec3f>(y,x)[0] < min_value)
// 					correction.at<Vec3f>(y,x)[0] = 0.;
// 				if (recent_reconstruction_convolved.at<Vec3f>(y,x)[1] < min_value)
// 					correction.at<Vec3f>(y,x)[1] = 0.;
// 				if (recent_reconstruction_convolved.at<Vec3f>(y,x)[2] < min_value)
// 					correction.at<Vec3f>(y,x)[2] = 0.;
// 			}
// 		}	
		
		multiply(recent_reconstruction,correction,recent_reconstruction);
	};
}

Mat Deconvolve::ApplyDFT(Mat input_image){
	Mat planes[] = {input_image, Mat::zeros(input_image.size(), CV_32F)};
    Mat complex_image;    //Complex plane to contain the DFT coefficients {[0]-Real,[1]-Img}
    merge(planes, 2, complex_image); // combine the elements of planes to the new 2-channel complexI
    dft(complex_image, complex_image);  // Applying DFT
	return complex_image;
};

Mat Deconvolve::ApplyInverseDFT(Mat input_image){
	Mat inverse_dft;
    dft(input_image, inverse_dft,  DFT_INVERSE + DFT_SCALE + DFT_REAL_OUTPUT);
	return inverse_dft;
};

float Deconvolve::PSF(int x, int y) {
	// calculate Distance
	float sigma = 0.8;
	float quad_distance = pow(x, 2) + pow(y, 2);
	float output_value = 1 / (2*PI*pow(sigma,2)) * exp( - quad_distance / (2 * pow(sigma,2)));
	return output_value;
};

Mat Deconvolve::KernelSimulatedPSF(int scale_factor, int resize_interpolation) {
// 	int kernelSize = 13;
	
	// create small kernel with zeros and one 1 in center
	//int smallKernelSize = ceil((float)kernelSize / (float)scale_factor); // Ceil so that result will be odd
	int small_kernel_size = 5;
	int center_position = (small_kernel_size - 1) / 2;
	
	Mat small_kernel = Mat::zeros(small_kernel_size, small_kernel_size, CV_32F);
	   small_kernel.at<float>(center_position, center_position) = 1.;
	
	// Preconvolve with gaussian to simulate initial blur of images
	//GaussianBlur(smallKernel, smallKernel, Size(0,0), 1.);
	
	// upscale the small kernel to the actual kernel size
	int kernel_size = small_kernel_size * scale_factor;
	Mat kernel(kernel_size, kernel_size, CV_32F);
	resize(small_kernel, kernel, kernel.size(), 0, 0, resize_interpolation);
	
	// Apply box blur with the size of scale_factor
	Mat kernel_box_blur = Mat::ones(scale_factor, scale_factor, CV_32F);
	   kernel_box_blur /= (float)scale_factor * (float)scale_factor;  // Normalization
	//cout << "kernel";
	filter2D(kernel,kernel,-1,kernel_box_blur);
	
	// Normalize kernel
	divide(kernel, sum(kernel), kernel);
	
	// find maximum as anchor point
// 	Point * maxLocPtr = &maxLoc;
// 	minMaxLoc(kernel, NULL, NULL, NULL, maxLocPtr);
	
	return kernel;
	
};

Mat Deconvolve::CalculateKernel() {
	// Get image size
	// int imageWidth = image.cols;
	// int imageHeight = image.rows;
	int kernel_width = 5;
	int kernel_height = kernel_width;
	
	// Calculate Coordinates of image center
	int center_x = (kernel_width - 1) / 2;
	int center_y = (kernel_height - 1) / 2;
	
	// Create the Kernel image using the PSF
	Mat kernel = Mat::zeros(kernel_height, kernel_width, CV_32F);
	for ( int x = 0; x < kernel_width; x++) {
		for (int y = 0; y < kernel_height; y++) {
			int center_coordinates_x = x - center_x;
			int center_coordinates_y = y - center_y;
			
			float kernel_value = PSF(center_coordinates_x, center_coordinates_y);
			kernel.at<float>(y,x) = kernel_value;
			//kernel.at<float>(yCenterCoordinates, xCenterCoordinates) = 0;
		}
	}
	
	return kernel;
};
