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
#include <opencv2/opencv.hpp>
#include <string>
#include <algorithm>
#include <sstream>
#include <vector>

using namespace std;
using namespace cv;

# define PI           3.14159265358979323846

class Deconvolve {
public:
	Mat CalculateKernel();
	void DeconvolveLucy(Mat &recent_reconstruction, const Mat &kernel);
	void DeconvolveGoldMeinel(Mat &recent_reconstruction, const Mat &kernel); 
	Mat KernelSimulatedPSF(int scale_factor, int resize_interpolation);
private:	
	Mat ApplyDFT(Mat input_image);
	Mat ApplyInverseDFT(Mat input_image);
	float PSF(int x, int y);
};
