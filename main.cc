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
#include <string>
#include "src/verysharp_gui.h"
#include <gtkmm/application.h>

using namespace Gtk;

int main(int argc, char **argv) {
	auto app = Gtk::Application::create(argc, argv, "org.wilecoyote.photomerger");
	VerySharpApplication very_sharp_app;

	
	return app->run(very_sharp_app);
}
