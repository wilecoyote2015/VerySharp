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


#include <iostream>
#include "deconvolve.h"
//#include <opencv2/highgui.hpp>
#include <opencv2/opencv.hpp>
#include <string>
#include <algorithm>
#include <sstream>
#include <vector>
#include <gtkmm.h>

using namespace std;
using namespace cv;

# define PI           3.14159265358979323846


class PhotoMerger
{
public:
	PhotoMerger();
	PhotoMerger(int tile_size, float scale_factor) : 
		tile_size_(tile_size), 
		scale_factor_(scale_factor) 
		{continue_processing_ = true;};
  	bool LoadPhotos (vector<string> input_paths);
  	bool MergePhotos (Glib::Dispatcher* dispatcher_progress, Glib::Dispatcher* dispatcher_error, string output_path);
	void StopProcessing();
	double GetProgress();
	bool CheckIfProcessing();

private:
	void NormalizeAndInvert(float min_value, float max_value, Mat &image);
	Mat LoadPhoto (string inputPath);
	Mat CalcOpticalFlowMask(Mat &first_image, Mat &second_image);
	bool is_processing_;
	bool continue_processing_;
	bool error_occured_;
	double progress_;
  	vector<Mat> developed_images_;
  	int image_width_, image_height_, tile_size_;
	float scale_factor_;
//   	void showImage(Mat image);
  	int WriteImage(string outputPath, Mat image); //TODO with filepath
	void ProcessTile(
			int tile_size_difference,
			int tile_size_with_margin, 
			int x_tile_number, 
			int y_tile_number,
			int width_reference_image,
			int height_reference_image,
			int num_photos,
			TermCriteria criteria,
			int resize_interpolation,
			Mat &output_image
			) ;
	void CalculateRects (
		Rect &rect_output_tile, 
		Rect &rect_upscaled_tile_without_margin,
		Rect &rect_tile_with_margin,
		int &width_recent_tile_with_margin,
		int &height_recent_tile_with_margin,
		int width_reference_image,
		int height_reference_image,
		int tile_size_difference,
		int x_tile_number,
		int y_tile_number) ;
};

