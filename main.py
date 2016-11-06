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

# @todo: the script should take the input directory, output file and the
# monitoring directory per argument optionally. If those are given, the values in 
# the config variable are overwritten

# Scripts for making the subfolders for the data and iterate through them while
# executing this script!

# @todo: not for this project, but just to be complete: write proper fits headers
# by carrying over the data from the input file's headers and modifying it.

import sys
import MainWindow
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    main_window = MainWindow.MainWindow()
    main_window.show()
    
    sys.exit(app.exec_())



print ("finished")