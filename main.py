# -*- coding: utf-8 -*-
"""
Created on Wed Sep 21 23:24:40 2016

@author: wile
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