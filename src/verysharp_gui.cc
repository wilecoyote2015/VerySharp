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


#include "verysharp_gui.h"

VerySharpApplication::VerySharpApplication() : dispatcher_progress_(), dispatcher_processing_error_()
{
	merger_ = PhotoMerger(1024, 1.4);
	
	last_input_folder_ = "";
	last_output_folder_ = "";
	output_path_ = "";
	
	// Set window border width
	set_border_width(10);
	
	//setup box1
	box1_.set_spacing(10);
	box1_.set_orientation(Gtk::ORIENTATION_VERTICAL);
	
	// Setup loaded files list
	files_list_input_buffer_ = Gtk::TextBuffer::create();
	files_list_input_buffer_->set_text("Input files");
	files_list_view_.set_buffer(files_list_input_buffer_);
	files_list_view_.set_editable(false);
	files_list_view_.show();
	scrolled_window_fileslist_.add(files_list_view_);
	scrolled_window_fileslist_.set_policy(Gtk::POLICY_AUTOMATIC, Gtk::POLICY_AUTOMATIC);
	scrolled_window_fileslist_.set_size_request(400,200);
	box1_.pack_start(scrolled_window_fileslist_);
	scrolled_window_fileslist_.show();
	
	// Setup output file textview
	output_filename_buffer_ = Gtk::TextBuffer::create();
	output_filename_buffer_->set_text("Output file");
	output_file_view_.set_buffer(output_filename_buffer_);
	output_file_view_.set_editable(false);
	output_file_view_.set_size_request(-1,600);
	output_file_view_.show();
	scrolled_window_outputfile_.add(output_file_view_);
	scrolled_window_outputfile_.set_policy(Gtk::POLICY_AUTOMATIC, Gtk::POLICY_AUTOMATIC);
	box1_.pack_start(scrolled_window_outputfile_);
	scrolled_window_outputfile_.show();
	
	// Setup Progress bar
	progress_bar_.show();
	progress_bar_.set_fraction(0.0);
	box1_.pack_start(progress_bar_);
	
	// Setup process button
	button_process_.add_label("Process");
	button_process_.signal_clicked().connect(sigc::mem_fun(*this, &VerySharpApplication::OnButtonProcessClicked));
	buttonbox_.add(button_process_);
	button_process_.show();
	
	// Setup cancel button
	button_cancel_.add_label("Cancel");
	button_cancel_.signal_clicked().connect(sigc::mem_fun(*this, &VerySharpApplication::OnButtonCancelClicked));
	button_cancel_.set_sensitive(false);
	buttonbox_.add(button_cancel_);
	button_cancel_.show();
	
	// Setup image selection Button
	button_fileselect_.add_label("Select Images");
	button_fileselect_.signal_clicked().connect(sigc::mem_fun(*this, &VerySharpApplication::OnButtonFileselectClicked));
	buttonbox_.add(button_fileselect_);
	button_fileselect_.show();
	
	// Setup output selection Button
	button_outputselect_.add_label("Set output");
	button_outputselect_.signal_clicked().connect(sigc::mem_fun(*this, &VerySharpApplication::OnButtonOutputSelectClicked));
	buttonbox_.add(button_outputselect_);
	button_outputselect_.show();
	
	// Setup help Button
	button_help_.add_label("Help");
	button_help_.signal_clicked().connect(sigc::mem_fun(*this, &VerySharpApplication::OnButtonHelpClicked));
	buttonbox_.add(button_help_);
	button_help_.show();
	
	// Setup buttonbox TODO: set layout to horizontal explicitly
	buttonbox_.show(); 
	buttonbox_.set_spacing(10);
	box1_.pack_end(buttonbox_);
	
	add(box1_);
	box1_.show();
	
	// Connect handle to dispatcher for progressbar updates and error handling
	dispatcher_progress_.connect(sigc::mem_fun(*this, &VerySharpApplication::OnNotificationFromWorkerThread));
	dispatcher_processing_error_.connect(sigc::mem_fun(*this, &VerySharpApplication::OnNotificationProcessingError));
};


VerySharpApplication::~VerySharpApplication()
{
};


void VerySharpApplication::OnButtonProcessClicked() 
{
	if (input_paths_.size() < 2) {
		Gtk::MessageDialog dialog(*this, "Not enough images given");
		dialog.set_secondary_text("Please select at least two images to process.");
		dialog.run();
	} else if (output_path_ == ""){
		Gtk::MessageDialog dialog(*this, "No output file set");
		dialog.set_secondary_text("Please set an output file.");
		dialog.run();
	} else {
		// Disable/Enable buttons
		button_cancel_.set_sensitive(true);
		button_process_.set_sensitive(false);
		
		dispatcher_progress_.emit();
		progress_bar_.set_fraction(0.);
		
		// Try to load the Photos
		try {
			merger_.LoadPhotos(input_paths_);
		} catch (int e) {
			Gtk::MessageDialog dialog(*this, "Could not load images");
			string dialog_text = "Images could not be loaded. Exception number " + to_string(e);
			dialog.set_secondary_text(dialog_text);
			dialog.run();
		}
		
		merger_thread_= new std::thread(
			[this]
			{
				merger_.MergePhotos(&(this->dispatcher_progress_), &(this->dispatcher_processing_error_), this->output_path_);
			});
	}
};


void VerySharpApplication::OnButtonFileselectClicked() 
{
	Gtk::FileChooserDialog dialog ("Please choose at least two images with identical size", Gtk::FILE_CHOOSER_ACTION_OPEN);
	dialog.set_transient_for(*this);
	dialog.set_select_multiple(true);
	
	// Extensions for filters
	vector<string> supported_image_formats = {"jpg", "jpeg", "JPG", "jpe", "bmp", "dib", "jp2", "png", "tiff", "tif", "ppm", "pgm", "pbm"};
	
	// filter for image files so that only images are shown
	auto filter_images = Gtk::FileFilter::create();
	filter_images->set_name("Image files");
	for (vector<string>::iterator extension_iterator = supported_image_formats.begin(); extension_iterator != supported_image_formats.end(); ++extension_iterator)
	{
		string pattern = "*." + *extension_iterator;
		filter_images->add_pattern(pattern);
	}
	dialog.set_filter(filter_images);
	
	dialog.add_button("_Cancel", Gtk::RESPONSE_CANCEL);
	dialog.add_button("Select", Gtk::RESPONSE_OK);
	
	// Set the current folder to the last opened folder
	if (last_input_folder_ != "") {
		dialog.set_current_folder_uri(last_input_folder_);
	} else if (last_output_folder_ != "") {
		dialog.set_current_folder_uri(last_output_folder_);
	}
	
	int result = dialog.run();
	
	//Handle the response:
	if (result == Gtk::RESPONSE_OK)
	{
		// Get the filenames from the dialog
		input_paths_.clear();
		input_paths_ = dialog.get_filenames();
		
		// Set the last input folder
		last_input_folder_ = dialog.get_current_folder_uri();
		
		// String to store list of loaded files
		string files_list_string  = "";
		
		for (vector<string>::iterator inputPathIterator = input_paths_.begin(); inputPathIterator != input_paths_.end(); ++inputPathIterator)
		{
			// Add file name to the files list
			files_list_string += *inputPathIterator + "\n";
			
			// Append folder path to filenames to obtain filepaths
			//*inputPathIterator = uri_directory + "/" + *inputPathIterator; // TODO for windows maybe it is a backslash
		}
		
		// Insert files list into textview buffer
		files_list_input_buffer_->set_text(files_list_string);
	}
};


void VerySharpApplication::OnButtonOutputSelectClicked()
{	
	Gtk::FileChooserDialog dialog ("Please set an output file without extension", Gtk::FILE_CHOOSER_ACTION_SAVE);
	dialog.set_transient_for(*this);
	
	//TODO filters for image files
	
	dialog.add_button("_Cancel", Gtk::RESPONSE_CANCEL);
	dialog.add_button("Select", Gtk::RESPONSE_OK);
	
	// Set the current folder to the last opened folder
	if (last_output_folder_ != "") {
		dialog.set_current_folder_uri(last_output_folder_);
	} else if (last_input_folder_ != "") {
		dialog.set_current_folder_uri(last_input_folder_);
	}
	
	int result = dialog.run();
	
	//Handle the response:
	if (result == Gtk::RESPONSE_OK)
	{
		// Set the last output folder
		string current_folder = dialog.get_current_folder();
		last_output_folder_ = current_folder;
		
		output_path_ = current_folder + "/" + dialog.get_current_name() + ".jpg"; // TODO for windows maybe it is a backslash

		// Insert output path into textview buffer
		output_filename_buffer_->set_text(output_path_);
		cout << output_path_;
	}
}


void VerySharpApplication::OnButtonCancelClicked()
{
	button_cancel_.set_label("Canceling...");
	merger_.StopProcessing();
	progress_bar_.set_fraction(0.0);
}

void VerySharpApplication::OnButtonHelpClicked()
{
	string help_text =
		"This program combines a series of handheld-shot photos into an image with doubled resolution and "
		"greatly reduced moire and noise. "
		"In the following, a short guide on how to obtain optimal results is given:\n"
		"\n"
		"1. Shooting photos:\n"
		"Capture a series of six images of your subject with identical exposure. Do NOT use a tripod because VerySharp calculates "  
		"the extended image information based on little shifts between the individual images. "
		"Hold the camera as steadily as possible. For now, processing will only work properly for static subjects. Use RAW format.\n"
		"\n"
		"2. Preprocessing the Images\n"
		"Use your favorite RAW converter and process the Images to taste. Use the identical settings for all images so that they look the same. "
		"It is important to turn off sharpening. "
		"Turn on lens corrections like vignetting, CA and distortion correction.\n"
		"\n"
		"3. Using verysharp\n"
		"Start VerySharp and select the preprocessed images using the Select Images button. "
		"Define the output file using the Set Output button. "
		"Start processing using the Process button. The process will take some time.\n"
		"\n"
		"4. Have fun! \n"
		"For further information visit https://wilecoyote2015.github.io/VerySharp/ \n"
		"\n \n"
		"copyright (c) 2016 Björn Sonnenschein. \n"
		"\n"
		"verysharp is free software: you can redistribute it and/or modify\n"
		"it under the terms of the GNU General Public License as published by\n"
		"the Free Software Foundation, either version 3 of the License, or\n"
		"(at your option) any later version.\n"
		"\n"
		"verysharp is distributed in the hope that it will be useful,\n"
		"but WITHOUT ANY WARRANTY; without even the implied warranty of\n"
		"MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n"
		"GNU General Public License for more details.\n"
		"\n"
		"You should have received a copy of the GNU General Public License\n"
		"along with verysharp.  If not, see <www.gnu.org/licenses/>.\n"
		"\n";
	
	Gtk::MessageDialog dialog(*this, "Help", false );
	dialog.set_secondary_text(help_text);
	dialog.run();
}


void VerySharpApplication::OnNotificationProcessingError()
{
	Gtk::MessageDialog dialog(*this, "Processing Failed", false);
	dialog.set_secondary_text("Error during processing. \n Do all images have the same dimensions?");
	dialog.run();
}


void VerySharpApplication::OnNotificationFromWorkerThread()
{
	// Check if Merger is still working and set buttons
	if (!merger_.CheckIfProcessing()) {
		button_cancel_.set_sensitive(false);
		button_process_.set_sensitive(true);
		progress_bar_.set_fraction(0.);
		button_cancel_.set_label("Cancel");
	} else {
		// Update Progress Bar
		double progress = merger_.GetProgress();
		progress_bar_.set_fraction(progress);
	}
	
}

