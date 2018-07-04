#-------------------------------------------------------------------------------
# Name:        _RCD30_quickThumbs_v0.1.py
#
# Purpose:     This script is to be run in the Session
#              Thisscript will run either from a bat file or running from an IDE with the Project Environment set to
#			    C:\Anaconda\python.exe after navigating to the correct folder.
#
#               The script creates resized/resampled jpgs for use in Google Earth KML/KMZ.  It also
#				creates and file for viewing images along with point in ABE PFM3DEditor by adding the unix timestamp to
#				CameraSync*.dat file
#
# Requirements:  Google Earth; IrFanView (installed at C:\IrfanView); Python 2.7 (standard library)
#				 affine, pyproj, numpy, pandas,
#
#
# Author:      J. Heath Harwood; Modified from Jon Sellars DSS_quickThumbs64bit.py
#
# Created:     07/04/2018
# Copyright:   (c) USACE 2018
# Licence:     Public
#

#-------------------------------------------------------------------------------