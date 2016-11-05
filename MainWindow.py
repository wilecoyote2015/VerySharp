#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov  5 20:15:18 2016

@author: wile
"""

from PyQt5.QtWidgets import (QWidget, QPushButton, QLineEdit, QFileDialog,
                             QHBoxLayout, QVBoxLayout, QMessageBox, QListWidget)
from PyQt5.QtGui import QIcon
import configparser
import ImageStacker
import cv2

# TODO: make input and output dialog folders persistent!

class MainWindow(QWidget):
    
    def __init__(self):
        super().__init__()
        
        # read the config file todo: if config does not exist, create it.
        config_file_path = "./config.cfg"
        self.config = configparser.ConfigParser()
        self.config.read(config_file_path)
        
        self.output_file_field = None
        self.filepaths = None
        
        self.initUI()
        
        
    def initUI(self):
        
        button_process = QPushButton('Process', self)
        button_process.clicked.connect(self.startProcessing)
        
        button_select_files = QPushButton('Select Images', self)
        button_select_files.clicked.connect(self.selectInputFiles)
        
        button_select_output_file = QPushButton('Set Output', self)
        button_select_output_file.clicked.connect(self.selectOutputFile)
        
        button_help = QPushButton('Help', self)
        button_help.clicked.connect(self.showHelpBox)
        
        self.setWindowIcon(QIcon('./Icons/vsIcon.png')) 
        
        hbox_buttons = QHBoxLayout()
        hbox_buttons.addWidget(button_select_files)
        hbox_buttons.addWidget(button_process)
        hbox_buttons.addStretch(1)
        hbox_buttons.addWidget(button_help)
        
        hbox_inputfiles = QHBoxLayout()
        self.input_files_list = QListWidget(self)
        hbox_inputfiles.addWidget(self.input_files_list)

        hbox_outputfile = QHBoxLayout()
        self.output_file_field = QLineEdit()
        hbox_outputfile.addWidget(self.output_file_field)
        hbox_outputfile.addWidget(button_select_output_file)
        
        vbox = QVBoxLayout()
        vbox.addLayout(hbox_inputfiles)
        vbox.addLayout(hbox_outputfile)
        vbox.addLayout(hbox_buttons)
        
        self.setGeometry(300, 300, 300, 220)
        self.setWindowTitle('VerySharp')
        self.setLayout(vbox) 
        
    def selectInputFiles(self):
        filter_images = ("Images (*jpg *jpeg *JPG *jpe *bmp *dib *jp2 *png *tiff *tif *ppm *pgm *pbm)")
        filepaths = QFileDialog.getOpenFileNames(self,
                                                 "Select Images", 
                                                 filter=filter_images)[0]
                                                 
        self.filepaths = []
        for filepath in filepaths:
            self.filepaths.append(str(filepath))
            
        self.input_files_list.clear()
        print(self.filepaths)
        for input_path in filepaths:
            self.input_files_list.addItem(input_path)
#        self.filepaths = QFileDialog.getOpenFileName(self,
#                                                'Select Files',
#                                                filter=filter_images)[0]
        
    def selectOutputFile(self):
        output_file = QFileDialog.getSaveFileName(self, 'Set Output')[0]
        self.output_file_field.setText(output_file)
        
        
    def startProcessing(self):
        output_path = str(self.output_file_field.text())
        if self.filepaths is not None and output_path != "":
            stacker = ImageStacker.ImageStacker()
            processed_image = stacker.stackImages(self.filepaths)
            cv2.imwrite(output_path, processed_image)
        else:
            self.showMissingPathsDialog()
        
    def showMissingPathsDialog(self):
        QMessageBox.information(self, 'No files specifies',
        "Please select the input and output files.")
            
            
    def showHelpBox(self):
        
        help_text = ("This program combines a series of handheld-shot photos into an image with doubled resolution and "
		+ "greatly reduced moire and noise. "
		+ "In the following, a short guide on how to obtain optimal results is given:\n"
		+ "\n"
		+ "1. Shooting photos:\n"
		+ "Capture a series of six images of your subject with identical exposure. Do NOT use a tripod because VerySharp calculates "
		+ "the extended image information based on little shifts between the individual images. "
		+ "Hold the camera as steadily as possible. For now, processing will only work properly for static subjects. Use RAW format.\n"
		+ "\n"
		+ "2. Preprocessing the Images\n"
		+ "Use your favorite RAW converter and process the Images to taste. Use the identical settings for all images so that they look the same. "
		+ "It is important to turn off sharpening. "
		+ "Turn on lens corrections like vignetting, CA and distortion correction.\n"
		+ "\n"
		+ "3. Using verysharp\n"
		+ "Start VerySharp and select the preprocessed images using the Select Images button. "
		+ "Define the output file using the Set Output button. "
		+ "Start processing using the Process button. The process will take some time.\n"
		+ "\n"
		+ "4. Have fun! \n"
		+ "For further information visit https://wilecoyote2015.github.io/VerySharp/ \n"
		+ "\n \n"
		+ "copyright (c) 2016 Björn Sonnenschein. \n"
		+ "\n"
		+ "verysharp is free software: you can redistribute it and/or modify\n"
		+ "it under the terms of the GNU General Public License as published by\n"
		+ "the Free Software Foundation, either version 3 of the License, or\n"
		+ "(at your option) any later version.\n"
		+ "\n"
		+ "verysharp is distributed in the hope that it will be useful,\n"
		+ "but WITHOUT ANY WARRANTY; without even the implied warranty of\n"
		+ "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n"
		+ "GNU General Public License for more details.\n"
		+ "\n"
		+ "You should have received a copy of the GNU General Public License\n"
		+ "along with verysharp.  If not, see <www.gnu.org/licenses/>.\n"
		+ "\n")
        
        QMessageBox.information(self, 'Help',
        help_text)