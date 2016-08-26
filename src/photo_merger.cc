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


#include "photo_merger.h"
//#include "PhotoMergerGUI.h"

// TODO Don't load all photos, but only the one that is processed! But only if Photos are not raw!

PhotoMerger::PhotoMerger()
{
}


bool PhotoMerger::LoadPhotos (vector<string> input_paths)
{
	developed_images_.clear();

	// load all Photos into Buffers
	for (vector<string>::iterator iterator = input_paths.begin(); iterator != input_paths.end(); ++iterator)
	{	// develop the file
		Mat developed_image = imread(*iterator );
		Mat developed_image_float;
		developed_image.convertTo(developed_image_float, CV_32FC3);
		developed_images_.push_back(developed_image_float);
	}

	return true;
}


Mat PhotoMerger::LoadPhoto (string input_path)
{
	// load all Photos into Buffers
	Mat developed_image_float;
	Mat developed_image = imread(input_path);
	developed_image.convertTo(developed_image_float, CV_32FC3);

	return developed_image_float;
}


bool PhotoMerger::MergePhotos(Glib::Dispatcher* dispatcher_progress, Glib::Dispatcher* dispatcher_error, string output_path)
{
	cout << "Preparing photo Alignment" << "\n";
	is_processing_ = true;
	error_occured_ = false;

	try {
		// Load first Image as reference Image
		Mat reference_image = developed_images_[0];
		int num_photos = developed_images_.size();

		// Termination criteria for alignment
		int number_of_iterations = 5000;
		double termination_eps = 1e-5;
		TermCriteria criteria (TermCriteria::COUNT+TermCriteria::EPS, number_of_iterations, termination_eps);

		// calculate parameters for the output image
		int resize_interpolation = CV_INTER_LANCZOS4;
		int reference_image_width = reference_image.cols;
		int reference_image_height = reference_image.rows;
		int width_output_image = reference_image_width * scale_factor_;
		int height_output_image = reference_image_height * scale_factor_;

		// Tiling Properties
		int num_tiles_x = (int) ceil((float)reference_image_width / (float)tile_size_);
		int num_tiles_y = (int) ceil((float)reference_image_height / (float)tile_size_);

		// Properties of Tiles
		float tilesMargin = 0.1; // Margin of tiles as fraction of image size
		int tile_size_with_margin = tile_size_ * (1 + tilesMargin);
		int tile_size_difference = tile_size_with_margin - tile_size_; // calculate from tile_size_ to prevent possible rounding differences

		cout << "x tile count " << num_tiles_x << "\n";
		cout << "y tile count " << num_tiles_y << "\n";
		cout << "tile size " << tile_size_ << "\n";

		// create the output image as upscaled zero matrix
		Mat output_image; 
		output_image = Mat::zeros(height_output_image, width_output_image, CV_32FC3);
		
		// Prepare calculation of process
		progress_ = 0.;
		double max_progress = 1.;
		int num_tiles = num_tiles_x * num_tiles_y;
		double step_progress = max_progress / num_tiles;

		for (int x_tile_number = 1; x_tile_number < num_tiles_x && continue_processing_; x_tile_number++) {
			for (int y_tile_number = 0; y_tile_number < num_tiles_y && continue_processing_; y_tile_number++) {
				// Only continue if the process wasn't aborted by the user
				ProcessTile(
						tile_size_difference,
						tile_size_with_margin, 
						x_tile_number, 
						y_tile_number,
						reference_image_width,
						reference_image_height,
						num_photos,
						criteria,
						resize_interpolation,
						output_image
						);
				
				// Save the current state of the whole image
				//string output_path = "finalOutput.jpg";
				WriteImage(output_path, output_image);
				
				// Set the process
				progress_ += step_progress;
				dispatcher_progress->emit();
			}
		}
	} catch (...) {
		dispatcher_error->emit();
	}
	
	is_processing_ = false;
	continue_processing_ = true;
	dispatcher_progress->emit();
	progress_ = 0.;
	return true;
};


void PhotoMerger::ProcessTile(
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
			)
{
	// copy Tile Size with margin because this value will be altered according to boundary conditions
	int height_recent_tile_with_margin = tile_size_with_margin;
	int width_recent_tile_with_margin = tile_size_with_margin;
	
	cout << "Calculating Tile X:" << x_tile_number << " Y:" << y_tile_number << "\n";

	// create Rects for ROIs 
	Rect rect_output_tile, rect_upscaled_tile_without_margin, rect_tile_with_margin;
	CalculateRects(
		rect_output_tile, 
		rect_upscaled_tile_without_margin,
		rect_tile_with_margin,
		width_recent_tile_with_margin,
		height_recent_tile_with_margin,
		width_reference_image,
		height_reference_image,
		tile_size_difference,
		x_tile_number,
		y_tile_number);

	// Calculate dimensions of Tiles
	int height_upscaled_tile_with_margin = round(height_recent_tile_with_margin * scale_factor_);
	int width_upscaled_tile_with_margin = round(width_recent_tile_with_margin * scale_factor_);
	
	// Create the upscaled reference Tile with margin 
	Mat tile_reference_with_margin(developed_images_[0], rect_tile_with_margin);
	Mat tile_reference_with_margin_upscaled = Mat(height_upscaled_tile_with_margin, width_upscaled_tile_with_margin, CV_32FC3);
	resize(tile_reference_with_margin, tile_reference_with_margin_upscaled, tile_reference_with_margin_upscaled.size(), 0, 0, resize_interpolation);
	
	// Create Tile with zeros which will hold the processed Tile
	Mat tile_processed_with_margin = Mat::zeros(height_upscaled_tile_with_margin, width_upscaled_tile_with_margin, CV_32FC3);
	
	// create ROI of the processed tile without margin which will be used to insert the processed tile into outputTile
	Mat tile_processed_without_margin(tile_processed_with_margin, rect_upscaled_tile_without_margin);

	// Create output Tile which will be used to insert the processed Tile into the Image
	Mat tile_output(output_image, rect_output_tile);
	
	// Insert the reference Tile into tile_processed_with_margin
	tile_processed_with_margin += tile_reference_with_margin_upscaled / num_photos;

	// Create 8UC1 Representation of the scaled reference Tile
	Mat tile_reference_with_margin_upscaled_8UC3, tile_reference_with_margin_upscaled_8UC1;
	tile_reference_with_margin_upscaled.convertTo(tile_reference_with_margin_upscaled_8UC3, CV_8UC3);
	cvtColor(tile_reference_with_margin_upscaled_8UC3, tile_reference_with_margin_upscaled_8UC1, CV_RGB2GRAY);

	// Set the previous tile for optical flow calculation
	// Mat tile_previous_with_margin_upscaled_8UC1 = tile_reference_with_margin_upscaled_8UC1;
	
	// Loop through images
	int image_counter = 1;
	for (vector<Mat>::iterator image_recent = developed_images_.begin() + 1; image_recent != developed_images_.end() && continue_processing_; ++image_recent)
	{
		cout << "Aligning Tile of image " << image_counter << " of " << num_photos - 1 << "\n" ;

		// Create scaled tile ROI with margin from recent Image
		Mat tile_recent_image_with_margin(*image_recent, rect_tile_with_margin);
		Mat tile_recent_image_with_margin_upscaled = Mat(height_upscaled_tile_with_margin, width_upscaled_tile_with_margin, CV_32FC3);
		resize(tile_recent_image_with_margin, tile_recent_image_with_margin_upscaled, tile_recent_image_with_margin_upscaled.size(), 0, 0, resize_interpolation);
		
		// Create 8UC1 Representation of the scaled recent image Tile
		Mat tile_recent_image_with_margin_upscaled_8UC3, tile_recent_image_with_margin_upscaled_8UC1;
		tile_recent_image_with_margin_upscaled.convertTo(tile_recent_image_with_margin_upscaled_8UC3, CV_8UC3);
		cvtColor(tile_recent_image_with_margin_upscaled_8UC3, tile_recent_image_with_margin_upscaled_8UC1, CV_RGB2GRAY);

		// Find best transformation for optimal overlay
		Mat transformation_matrix = estimateRigidTransform(tile_reference_with_margin_upscaled_8UC3, tile_recent_image_with_margin_upscaled_8UC3, true); // Get rough estimate
		transformation_matrix.convertTo(transformation_matrix, CV_32FC1); // Convert the 64 bit to 32 bit float
		findTransformECC(tile_reference_with_margin_upscaled_8UC1, tile_recent_image_with_margin_upscaled_8UC1, transformation_matrix, MOTION_EUCLIDEAN, criteria);
		
		// Apply the Transformation
		warpAffine( tile_recent_image_with_margin_upscaled, tile_recent_image_with_margin_upscaled, transformation_matrix, tile_recent_image_with_margin_upscaled.size(), CV_INTER_LANCZOS4 + WARP_INVERSE_MAP);
		
// 		// TODO: Calculate, normalize and invert Optical flow mask
// 		float min_flow_value = 11.;
// 		float max_flow_value = 12.;
// 		Mat optical_flow_magnitude = CalcOpticalFlowMask(tile_reference_with_margin_upscaled_8UC1, tile_recent_image_with_margin_upscaled_8UC1);
// 		NormalizeAndInvert(min_flow_value, max_flow_value, optical_flow_magnitude);
// 		WriteImage("Flow.jpg", optical_flow_magnitude);
// 		
// 		// TODO: Multiply the processed tile with optical flow mask
// 		Mat optical_flow_magnitude_32FC3;
// 		//optical_flow_magnitude.convertTo(optical_flow_magnitude_32FC3, CV_32FC3);
// 		cvtColor(optical_flow_magnitude, optical_flow_magnitude_32FC3, CV_GRAY2BGR);
// 		cout << optical_flow_magnitude_32FC3.type() << "\n" << tile_recent_image_with_margin_upscaled.type() << "\n";
// 		multiply(tile_recent_image_with_margin_upscaled, optical_flow_magnitude_32FC3, tile_recent_image_with_margin_upscaled);
		
		// TODO: Add optical flow mask to the weight mask
		
		// Add the recent Image's Tile to the tile_processed_with_margin
		tile_processed_with_margin += tile_recent_image_with_margin_upscaled / num_photos;
		
		// Set the recent tile as previous tile for next number_of_iterations
		// tile_previous_with_margin_upscaled_8UC1 = tile_recent_image_with_margin_upscaled_8UC1;
		
		image_counter++;
	}
		
	if (continue_processing_) {
		// TODO: Multiply the Tile with the weight mask
		
		//deblur the Tile with margin
		cout << "deconvolving tile \n";
		Deconvolve deconvolver;
		Mat kernel = deconvolver.CalculateKernel();
		//deconvolver.DeconvolveLucy(tile_processed_with_margin, kernel);
		deconvolver.DeconvolveGoldMeinel(tile_processed_with_margin, kernel); //faster
		cout << "finished deconvolving tile \n";
		
		// Add the  processed Tile to the outputImage
		tile_output += tile_processed_without_margin;
		
// 		// Save the recent tile
// 		stringstream xTileNumberSS, yTileNumberSS;
// 		xTileNumberSS << xTileNumber;
// 		yTileNumberSS << yTileNumber;
// 		string out = "xTile" + xTileNumberSS.str() + "yTile" + yTileNumberSS.str()+ ".jpg";
// 		writeImage(out, tile_output);
	}
}


void PhotoMerger::CalculateRects (
		Rect &rect_output_tile, 
		Rect &rect_upscaled_tile_without_margin,
		Rect &rect_tile_with_margin,
		int &width_recent_tile_with_margin,
		int &height_recent_tile_with_margin,
		int width_reference_image,
		int height_reference_image,
		int tile_size_difference,
		int x_tile_number,
		int y_tile_number)  

{
	int tile_position_difference_x = 0;
	int tile_position_difference_y = 0;
	int tile_margin_in_pixels_x = tile_size_difference / 2;
	int tile_margin_in_pixels_y = tile_size_difference / 2;
	
	// Create tile Position
	int position_tile_x = round(tile_size_ * x_tile_number);
	int position_tile_y = round(tile_size_ * y_tile_number);
	
	// calculate position and size of tile with margins considering image boundaries
	int position_tile_with_margin_x = position_tile_x - tile_margin_in_pixels_x;
	int position_tile_with_margin_y = position_tile_y - tile_margin_in_pixels_y;
	if (position_tile_with_margin_x < 0){
		tile_position_difference_x = -position_tile_with_margin_x;
		width_recent_tile_with_margin += position_tile_with_margin_x;
		position_tile_with_margin_x = 0;
	}
	if (position_tile_with_margin_y < 0){
		tile_position_difference_y = -position_tile_with_margin_y;;
		height_recent_tile_with_margin += position_tile_with_margin_y;
		position_tile_with_margin_y = 0;
	}
	if (position_tile_with_margin_x + width_recent_tile_with_margin >= width_reference_image - 1){
		width_recent_tile_with_margin -= position_tile_with_margin_x + width_recent_tile_with_margin - width_reference_image;
	}
	if (position_tile_with_margin_y + height_recent_tile_with_margin >= height_reference_image - 1){
		height_recent_tile_with_margin -= position_tile_with_margin_y + height_recent_tile_with_margin - height_reference_image;
	}
	
	// calculate position and size of tile without margins considering image boundaries
	int size_tile_upscaled_without_margin = round(tile_size_ * scale_factor_);
	int width_tile_upscaled_without_margin = size_tile_upscaled_without_margin;
	int height_tile_upscaled_without_margin = size_tile_upscaled_without_margin;
	int position_tile_upscaled_x = size_tile_upscaled_without_margin * x_tile_number;
	int position_tile_upscaled_y = size_tile_upscaled_without_margin * y_tile_number;
	int width_image_upscaled = round(width_reference_image * scale_factor_);
	int height_image_upscaled = round(height_reference_image * scale_factor_);
	if (position_tile_upscaled_x + width_tile_upscaled_without_margin > width_image_upscaled - 1)
		width_tile_upscaled_without_margin -= position_tile_upscaled_x + width_tile_upscaled_without_margin - (width_image_upscaled - 1);
	if (position_tile_upscaled_y + height_tile_upscaled_without_margin > height_image_upscaled - 1)
		height_tile_upscaled_without_margin -= position_tile_upscaled_y + height_tile_upscaled_without_margin - (height_image_upscaled - 1);
	
	// Create reference Tile with Margins
	rect_tile_with_margin = Rect(
		position_tile_with_margin_x,
		position_tile_with_margin_y,
		width_recent_tile_with_margin,
		height_recent_tile_with_margin );

	// create Tile ROI from the output image
	rect_output_tile = Rect(
		position_tile_upscaled_x,
		position_tile_upscaled_y,
		width_tile_upscaled_without_margin,
		height_tile_upscaled_without_margin );
	
	// Create ROI from the referenceTile without margin
	int position_rect_tile_without_margin_x = round((tile_margin_in_pixels_x - tile_position_difference_x) * scale_factor_);
	int position_rect_tile_without_margin_y = round((tile_margin_in_pixels_y - tile_position_difference_y) * scale_factor_);
	rect_upscaled_tile_without_margin = Rect(
		position_rect_tile_without_margin_x,
		position_rect_tile_without_margin_y,
		width_tile_upscaled_without_margin,
		height_tile_upscaled_without_margin );
}

int PhotoMerger::WriteImage(string outputPath, Mat image) {
	Mat display_image;
	image.convertTo(display_image, CV_8UC3);
	imwrite( outputPath.c_str(), display_image);
	
	return 0;
};

void PhotoMerger::StopProcessing()
{
	continue_processing_ = false;
}

double PhotoMerger::GetProgress()
{
	return progress_;
}

bool PhotoMerger::CheckIfProcessing() {
	return is_processing_;
}

Mat PhotoMerger::CalcOpticalFlowMask(Mat &first_image, Mat &second_image)
{
		Mat optical_flow = Mat::zeros(first_image.size(), CV_32FC2); // Vecors!
		vector<Mat> optical_flow_components(2);
		Mat optical_flow_magnitude(first_image.size(), CV_32FC1);
		
		calcOpticalFlowFarneback(
			first_image, 
			second_image, 
			optical_flow,
			0.5,
			15,
			15,
			5,
			5,
			1.1,
			0);
		split(optical_flow, optical_flow_components);
		magnitude(optical_flow_components[0], optical_flow_components[1], optical_flow_magnitude);
		
		cout << optical_flow_magnitude.at<float>(260,740) << "\n";
		cout << optical_flow_magnitude.at<float>(592,1190) << "\n";
		
// 		WriteImage("Flow.jpg", optical_flow_magnitude);
		
		return optical_flow_magnitude;
}

void PhotoMerger::NormalizeAndInvert(float min_value, float max_value, cv::Mat& image)
{
	int image_width = image.cols;
	int image_height = image.rows;
	
	float max_possible_value = 1.;
	float value_range = max_value - min_value;
	
	for ( int x = 0; x < image_width; x++) {
		for (int y = 0; y < image_height; y++) {
			
			// Spread the values between min and max value
			float recent_value = image.at<float>(y,x);
			if (recent_value >= max_value) {
				recent_value = max_possible_value;
			} else if (recent_value <= min_value) {
				recent_value = 0;
			} else {
				recent_value = (recent_value - min_value) / value_range * max_possible_value;
			}
			
			// invert
			recent_value = max_possible_value - recent_value;
			
			// Assign the calculated value
			image.at<float>(y,x) = recent_value;
		}
	}	
	
	// Invert
	
}

