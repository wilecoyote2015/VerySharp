INC_DIR = ./src
LIB_DIR = /usr/lib
CFLAGS=-c -Wall -I$(INC_DIR) -L$(LIB_DIR)
DEPS = RawDeveloper.h PhotoMerger.h

all: main

main: main.o photo_merger.o deconvolve.o
	g++ -o vs_bin main.o photo_merger.o deconvolve.o verysharp_gui.o -lopencv_core -lopencv_video -lopencv_imgproc -lopencv_imgcodecs `pkg-config --cflags --libs gtkmm-3.0` # manual opencv include because highgui must not be included when compiled with gtk2

main.o: main.cc verysharp_gui.o
	g++  `pkg-config --cflags --libs gtkmm-3.0` $(CFLAGS) -c main.cc verysharp_gui.o

verysharp_gui.o: src/verysharp_gui.cc photo_merger.o
	g++ `pkg-config --cflags --libs gtkmm-3.0`  $(CFLAGS) -c src/verysharp_gui.cc photo_merger.o
	
photo_merger.o: src/photo_merger.cc deconvolve.o
	g++ `pkg-config --cflags --libs gtkmm-3.0` $(CFLAGS) -c src/photo_merger.cc deconvolve.o

deconvolve.o: src/deconvolve.cc
	g++ $(CFLAGS) -c src/deconvolve.cc

clean:
	rm -rf *.o
	rm -rf vs_bin
	
