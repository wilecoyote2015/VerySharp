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
//#include <gtkmm.h>
#include <gtkmm/button.h>
#include <gtkmm/window.h>
#include <gtkmm/messagedialog.h>
#include <gtkmm.h>
#include <gtkmm/buttonbox.h>
#include <gtkmm/box.h>
#include <iostream>
#include <thread>
// #include <string>

// using namespace Gtk;
using namespace std;

// TODO dialog to select output file

class VerySharpApplication : public Gtk::Window
{
public:
	VerySharpApplication();
	virtual ~VerySharpApplication();
	
protected:
	// Signal handlers
	void OnButtonProcessClicked();
	void OnButtonFileselectClicked();
	void OnButtonOutputSelectClicked();
	void OnButtonHelpClicked();
	void OnButtonCancelClicked();
	void OnNotificationFromWorkerThread();
	void OnNotificationProcessingError();
	
	// Member widgets
	Gtk::Button button_process_;
	Gtk::Button button_fileselect_;
	Gtk::Button button_outputselect_;
	Gtk::Button button_cancel_;
	Gtk::Button button_help_;
	Gtk::ButtonBox buttonbox_; 
	Gtk::Box box1_;
	Gtk::ProgressBar progress_bar_;
	Gtk::ScrolledWindow scrolled_window_fileslist_, scrolled_window_outputfile_;
	Gtk::TextView files_list_view_, output_file_view_;
	
	// Buffer for files_list_and output_file_view
	Glib::RefPtr<Gtk::TextBuffer> files_list_input_buffer_;
	Glib::RefPtr<Gtk::TextBuffer> output_filename_buffer_;
	
	Glib::Dispatcher dispatcher_progress_, dispatcher_processing_error_;
	
private:
	// Variables to restore the location of file dialogs
	string last_input_folder_;
	string last_output_folder_;
	
	// Paths
	vector<string> input_paths_;
	string output_path_;
	
	PhotoMerger merger_;
	std::thread* merger_thread_;
};
