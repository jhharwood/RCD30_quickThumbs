#-------------------------------------------------------------------------------
# Name:        _RCD30_quickThumbs64bit_20170718.py
#
# Purpose:     This script is to be run in the DC_* camera folder in the wks_local EFFORT Tree
#               For example, '''O:\2013_NCMP_Hawaii\13005_Oahu\processing\lidar_wks\Block_03\wks_local\EFFORT_2013ncmphi /n
#               \oahu_block_03a\CZ03MD13005_P_130919_0146\CZ03DS13005_P_130919_0146_A\DC_DS_P_130919_0146_A'''.  This
#               script will run either from a bat file or running from an IDE with the Project Environment set to  
#				C:\Anaconda\python.exe after navigating to the correct folder.
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
# Created:     09/29/2013
# Copyright:   (c) USACE 2013
# Licence:     Public
#

#-------------------------------------------------------------------------------

'''
Change log:
### Quick and dirty thumbnail Google overlay for the DSS
### Jon Sellars and Bang Le, NOAA, December, 2005
### Updated by Jon Sellars and Chris Parrish to Read CSV files to create JGW world files for DSS Images April 2006
### Ported from IDL to Python APR2008 Jon Sellars. JGW support dropped
### 0.6 single script for IR and RGB
### 0.7 regions and min level of detail added
### 0.8 kmz support added
### 0.8.2 year added as prefix to id
### 0.8.3 added support for elevation as a user input
### 0.8.4 C for RGB and R for IR changed
### 0.8.5 skip lines with "_" that are culled in premosaic.py
### quickThumbs March 2010: Extracts thumbnails from raw image data and creates
### a GoogleEarth kmz.
### depends on:
### c:\dcraw\dcraw.exe
### c:\IrfanView\i_view32.exe
### 0.8.6 Added compatibilty for linux (depends on dcraw and ppm2jpeg - 20100603
### 0.8.7 Added labels for the images - 20100613
### 0.8.8 Added the compatibility for Windows 64bit - 20110427
20130929 H. Harwood; tool is operational for USACE GSI Camera 
20160519 H. Harwood; tool is operational for USACE RCD30 Camera
20160905 C. Macon; adjusted kml output
20161103 H. Harwood; added CameraSync*_R.dat production for ChartsPic


TODO:
 -

'''

###>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.IMPORT STATEMENTs.>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>###

import re, Queue, threading
import os
import math
from math import *
from datetime import *
from time import *
import time
import fnmatch
import zipfile
import glob
import csv
import copy
from pyproj import Proj, transform
from affine import Affine
import numpy as np
import pandas as pd
import multiprocessing as mp

###>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.CONSTANTS.>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>###

# Scale factor 1 for full scale
scale = 1
scale = scale + 0.00000
#SF = 1/scale

# Level of detail to turn layer on
minlod = 1
# set this so that management types can't zoom in beyond 1:1
maxlod = -1
clip = 0.0 # A percent used to clip the region to limit the number of images that pop up

imgtype = 'C'
imgelev = -23.5
imgyear = 2018

FL = 0.053                  # FL= Focal Length in cm
CCD_X = 0.0540               # CCD_X = along track meters in m 0.006/9000
CCD_Y = 0.0404            # CCD_Y = across track meters Left Wing + in m
PP_X =  0.0078              # PP_X = Principle Point x(super)i from Terrestrial Cal Report/and or Boresite in m
PP_Y =  -0.0042             # PP_Y = Principle Point y(super)i from Terrestrial Cal Report/and or Boresite in m
PP_Pix_Y = 3366             # PP_Pix_X = Principle Point x(super)P off from upper left in pixel
PP_Pix_X = 4500             # PP_Pix_Y = Principle Point y(super)P off from uppper left in pixel
CCD_XY = 0.0000060          # CCD_XY pixel size on CCD array meters in m

PP_Pix_X = PP_Pix_X
PP_Pix_Y = PP_Pix_Y

Geoid = 0                   #Geoid ->Estimate for project area
Radius = 6378137            #Radius ->SemiMajor Radius of the Datum

# RCD30 coarse navigation parameters
BS_P = 5
BS_R = 8
BS_H = -0.5

# Set zone
#zoneNum = raw_input('\nWhat is the zone number?  Enter here: ')
zoneNum = 17
#zoneHem = raw_input('\nWhat is the zone hemisphere?  Enter here: ')
zoneHem = 'N'

WEEK_OFFSET = 7.0 * 86400.0
prev_time = -1


###>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.FUNCTIONS.>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>###
# Get local time/year
lt = time.localtime()
curryear = lt[0]

# Figure out where you are
cwd = os.getcwd()
cwf = os.path.basename(cwd)

# modify if not developing tifs
#imgs = cwd + "\\" + "Thumbnails" + "\\" + glob.glob('*.tif')

def getTifs(sessDir):
    # Get list of files in MGRS Grids directory
    sessList = os.listdir(sessDir)
    print sessList

    pattern = "_thumb_rgb"
    thumbList = []

    for file in sessList:
        if fnmatch.fnmatch(file, pattern+'.tif'):
            print "Added to file to thumbs list " + file
            thumbList.append(file)

    return thumbList

imgs = getTifs(cwd)
tot_file=len(imgs)
print tot_file


# Set this number appropriately; Number of CPUs minus 12.  Subtracte 1/3 of number of CPUs on the workstation
nProc = mp.cpu_count() - 12
irfSwCmd = []

print 'Processing thumbnails with irfanview'
for img in imgs:

    imgName = os.path.basename(img)
    imgIn = img
    imgOut = imgName.replace('.tif','_scaled.jpeg')
	
    if os.path.exists(r'c:\IrfanView\i_view64.exe'):
	    irfSw = (r'c:\IrfanView\i_view64.exe %s\%s /resize=(609,406) /resample /aspectratio /jpeg=75 /convert=%s\%s')%(cwd,imgIn,cwd,imgOut)
	    print irfSw
	    irfSwCmd.append(irfSw)
    else:
	    print "The IrfanView program i_view64.exe is missing or not in the correct path c:\IrfanView\i_view64.exe.\n"

    
queue = Queue.Queue()


class threadJobs(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # get job from queue
            myJob = self.queue.get()
            inCmd = myJob
            os.system(inCmd)

            # signal queue job is done
            self.queue.task_done()


def main():
    # spawn a pool of processes, and let the queue manage them
    for i in range(nProc):
        t = threadJobs(queue)
        t.setDaemon(True)
        t.start()
    # populate queue with jobs
    for cmd in irfSwCmd:
        queue.put(cmd)
    # wait on the queue until everything has been processed
    queue.join()
    # wait for processing to finish
    while not queue.empty():
        time.sleep(1)
    return 'Done'

main()

# Function calculates the picture time in unix time to add to the camera syn file
def getPictureTime(yr, mth, day, gps_seconds, prevTime):

    """
    :Pass the gps seconds of the image to get the unix time (picture time):
    :return:
    """

    try:

        # Define flight date using the folder name and strip the time to create a time struct
        flightDate = time.strptime((("%2s/%2s/%4s")%(mth,day,yr)), "%m/%d/%Y")

        # Get seconds from the epoch (01-01-1970) for the date in the filename. This will also give us the day of the
        # week for the GPS seconds of week calculation.
        tv_sec = time.mktime(flightDate)
        #print "GPS seconds from the epoch (01-01-1970) for the date in the filename :", tv_sec

        # Get flight date weekday
        flightDate_weekday = flightDate.tm_wday + 1
        if flightDate_weekday >= 7:
            flightDate_weekday = flightDate_weekday - 7
        #print "The flight day weekday is: ", flightDate_weekday
        # Subtract the number of days since Saturday midnight (Sunday morning) in seconds.
        tv_sec = tv_sec - (flightDate_weekday * 86400)
        start_week = tv_sec
        #print "Subtract the number of days since Saturday midnight (Sunday morning) in seconds. :", start_week
        #print "The number of GPS Seconds is: ", gps_seconds

        picture_time = (start_week + gps_seconds) * 1000000.0
        #print "The new Picture time is: ", str(int(picture_time))
        #print "The previous Picture time is: ", str(int(prevTime))

        # Test for GPS Week Rollover
        if int(picture_time) < int(prevTime):
            picture_time += WEEK_OFFSET * 1000000.0
            print "The picture time after week rollover is: %s" % str(int(picture_time))
            return str(int(picture_time))
        else:
            print "The picture time before week rollover is: %s" % str(int(picture_time))
            return str(int(picture_time))


    except IOError as e:                                                            # prints the associate error
        print "I/O Error %d: %s" % (e.errno, e.strerror)
        raise e


###>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.MAIN.>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>###

print "Processing data in: \n", cwd+"\n"

# Get year/month/day from the DC_DP camera folder name
# The data for NCMP/CZMIL collection is held in folders with the following nomenclature DC_DS_P_130919_0146_A as an example
# Year/Month/Date is parsed from this folder name.
# This variables can be hard coded and folder names could be changed if desired
# Gets the 13 from the array DC_DS_P_130919_0146_A
year = "20" + str(cwf[8:10])
# Gets the 09 from the array DC_DS_P_130919_0146_A
month = str(cwf[10:12])
# Gets the 19 from the array DC_DS_P_130919_0146_A
day = str(cwf[12:14])
print year, month, day

# Open the RCD30 coarse_lat_lon_ellHeight_roll_pitch_heading dat file and Event file
datFiles = glob.glob('*.dat')
for datFile in datFiles:
    datFile = datFile
    #print datFile

# Get the RCD30 Event file	
evtFiles = glob.glob('*.evt')
for evtFile in evtFiles:
    evtFile = evtFile
    #print evtFile

# Create a new output camera file that's merged with the event.evt and the coarse_lat_lon_ellHeight_roll_pitch_heading.dat
newDat = open((datFile.split('.')[0] + '_new' + '.dat'), 'w')

a1 = pd.read_csv(datFile, delimiter=r"\s+", header= None)
b1 = pd.read_csv(evtFile, delimiter=r"\s+", header= None)

# Merges the coarse* and event file
a1[8] = b1[0]

a1.to_csv(newDat,index=False,header=False, sep=' ')

newDat.close()

# Open the new camera dat file for reading
newDatFiles = glob.glob('*_new.dat')
for newDatFile in newDatFiles:
    newDatFile = newDatFile
    #print newDatFile

camDat = open(newDatFile, 'r')
#print camSYNCdat
ilist = camDat.readlines()
#print ilist

# Name the kml from the name of the common working directory "DC_*"
name2 = str(cwf)
#print name2

# Create the master kml file in the mission directory and open for writing.
print "Generating a KMZ file named: \n"+name2+"_thumbs.kmz\n"
kml = open(os.path.join(name2+"_thumbs.kml"), 'w')
#print kml

# Name the output files from the name of the common working directory "DC_*"
csfName = str(cwf[8:])
#print csfName

# Create the output camera sync file that will be used for RCD30 Image Index
cameraSync0 = open(("CameraSync_" + csfName + '_0.dat'), 'w')
### System number is used for chartsPic is actually not a system but instead not a hof/tof/CM4800 file and disgnates the RCD30 Camera
##sysNum0 = 'system_num 4'
##cameraSync0.writelines(sysNum0)
cameraSyncR = open(("CameraSync_" + csfName + '_R.dat'), 'w')
# System number is used for chartsPic is actually not a CZMIL system but instead not a hof/tof/CM4800 file and disgnates the RCD30 Camera
sysNumR = ' system_num 4\n'
cameraSyncR.writelines(sysNumR)
#print cameraSync

# Write out the KML header
khead = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.2">
<Document>
  <Style id="FEATURES_LABELS">
    <IconStyle>
      <color>FFFFFFFF</color>
      <Icon>
        <href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href>
      </Icon>
    </IconStyle>
    <LabelStyle>
      <color>FFFFFFFF</color>
    </LabelStyle>
  </Style>
  <Folder>
	<name>"""+name2+""" Thumbnails</name>\n"""

kml.writelines(khead)

# Start looping through dat Check for text to skip header.
print "Starting Overlay Loop..."

# Initialize a line counter
counter = 0
for iLine in ilist:

    # Increment counter
    counter += 1

    if counter > 1:  # New Camera dat file has a system number header that allows chartsPic to see that it's an RCD30 camera
        # Parse the data in the Camera dat file
        mylist = iLine.strip().split(' ')
        mylist = [item for item in mylist if item]

        pid = mylist[0]
        fileName = mylist[1].split('.')[0]
        iName = os.path.join(fileName + '_scaled.jpeg')
        Lat = float(mylist[3])
        latF = format(Lat, '.11f')
        Lon = float(mylist[2]) #- 360  # RCD30 65025 Sensor Head and FramePro being 3rd party we have to compensate for longitude being incorrect in an older version of FramePro
        lonF = format(Lon, '.11f')
        zed = float(mylist[4])
        zedF = format(zed, '.4f')
        pitch = float(mylist[6])
        pitchF = format(pitch, '.13f')
        roll = float(mylist[5])
        rollF = format(roll, '.13f')
        heading = float(mylist[7])
        headingF = format(heading, '.13f')
        gpsSeconds = float(mylist[8]) + 0  # Compensating for the GPS/UTC offset set to zero if not needed; we compensate for this in Ipas CO+ later on
        gpsSecondsF = format(gpsSeconds, '.5f')
        #picTime = getPictureTime(year, month, day, gpsSeconds, prev_time)
        #prev_time = picTime

        # Convert Lat and Lon to radians
        Latrad = radians(Lat)
        Lonrad = radians(Lon)

        # Convert Lat and Lon to meters
        X = (Radius * (cos(Latrad))) * Lonrad
        Y = Radius * Latrad

        # Calculate pixel size based on flying height
        FH=zed
        PixSz=(FH*CCD_XY)/FL

        # Calculate pixel size in degrees for X and Y diminsions
        PixSzY = (degrees(PixSz/Radius))
        PixSzX = degrees(PixSz/(Radius * (cos(Latrad))))

        # Convert degress to radians (using * !DTOR <pi/180 ~= 0.01745>) ****Note H2 is set above******
        Prad = radians(pitch + BS_P)
        Rrad = radians(roll + BS_R)
        Hrad = radians(heading + BS_H)

        # Calculate s_inv
        s_inv = 1/(FL/FH)

        # Create terms for the M matrix
        M11 = cos(Prad)*sin(Hrad)
        M12 = -cos(Hrad)*cos(Rrad)-sin(Hrad)*sin(Prad)*sin(Rrad)
        M13 = cos(Hrad)*sin(Rrad)-sin(Hrad)*sin(Prad)*cos(Rrad)
        M21 = cos(Prad)*cos(Hrad)
        M22 = sin(Hrad)*cos(Rrad)-(cos(Hrad)*sin(Prad)*sin(Rrad))
        M23 = (-sin(Hrad)*sin(Rrad))-(cos(Hrad)*sin(Prad)*cos(Rrad))
        M31 = sin(Prad)
        M32 = cos(Prad)*sin(Rrad)
        M33 = cos(Prad)*cos(Rrad)
        #print M11, M12, M13, M21, M22, M23, M31, M32, M33

        # Define p matrix using PP offsets (image center) (rotate to +X direction of flight along track, +Y left wing across track, -FL)
        Xi = PP_Y
        Yi = -1.00 * PP_X
        FLneg = -1 * FL

        # s_inv * M * p + T(GPSxyz)
        CP_X = (s_inv *(M11* Xi + M12 * Yi + M13 * FLneg)) + X
        CP_Y = (s_inv *(M21* Xi + M22 * Yi + M23 * FLneg)) + Y
        CP_Z = (s_inv *(M31* Xi + M32 * Yi + M33 * FLneg)) + FH

        # Calculate Upper left corner (from center) in mapping space (DIR FLT = +Y, Right Wing = +X), rotate, apply to center coords in mapping space
        ULX = (PixSz * PP_Pix_X) + CP_X
        ULY = (PixSz * PP_Pix_Y) + CP_Y
        LRX = CP_X - (PixSz * PP_Pix_X)
        LRY = CP_Y - (PixSz * PP_Pix_Y)

        # Convert CP_X and CP_Y to Degrees Lat and - Long
        # East and West appear switched but it is the way X and Y
        # are handeled in the image reference frame above
        East = (degrees(ULX/(Radius * cos(Latrad)))) #- 360
        North = (degrees(ULY/Radius))
        West = (degrees(LRX/(Radius * cos(Latrad)))) #- 360
        South = (degrees(LRY/Radius))

        # Calculated center point of lat and Long convereed to degrees
        CenLat = (degrees(CP_Y/Radius))
        CenLon = (degrees(CP_X/(Radius * cos(Latrad))))

        # Calculate Rotation
        if imgtype == "C" :
            Rot = heading
            if Rot >= 180 : Rotation = 360.00 - Rot
            if Rot < 180 : Rotation = -1.00 * (Rot * 1.00)
        if imgtype == "R" :
            Rot = heading + 180.0
            if Rot > 360 : Rot = Rot -360
            if Rot < 180 : Rotation = 360 - Rot
            if Rot >= 180 : Rotation = -1 * (Rot * 1)

        # Calculate the clip
        nsClip = (North - South) * clip
        ewClip = (West - East) * clip

        # Write to the master KML
        kbody = """  	<Document>
    	<name>"""+iName+"""</name>
    	<Region>
    		<LatLonAltBox>
                                <north>"""+str(North - nsClip)+"""</north>
                                <south>"""+str(South + nsClip)+"""</south>
                                <east>"""+str(East + ewClip)+"""</east>
                                <west>"""+str(West - ewClip)+"""</west>
    			<minAltitude>0</minAltitude>
    			<maxAltitude>0</maxAltitude>
    		</LatLonAltBox>
    		<Lod>
    			<minLodPixels>"""+str(minlod)+"""</minLodPixels>
    			<maxLodPixels>"""+str(maxlod)+"""</maxLodPixels>
    			<minFadeExtent>0</minFadeExtent>
    			<maxFadeExtent>0</maxFadeExtent>
    		</Lod>
    	</Region>
    	<Style>
    		<ListStyle id="hideChildren">
    			<listItemType>checkHideChildren</listItemType>
    			<bgColor>00ffffff</bgColor>
    		</ListStyle>
    	</Style>
    	<GroundOverlay>
    		<name>r08569772</name>
    		<Icon>
    			<href>"""+iName+"""</href>
    		</Icon>
    		<LatLonBox>
                        <north>"""+str(North)+"""</north>
                        <south>"""+str(South)+"""</south>
                        <east>"""+str(East)+"""</east>
                        <west>"""+str(West)+"""</west>
                        <rotation>"""+str(Rotation)+"""</rotation>
    		</LatLonBox>
    	</GroundOverlay>
    </Document>\n"""
        #print kbody
        kml.writelines(kbody)

kmiddle = """</Folder>
    <Folder>
    	<visibility>0</visibility>
	<name>"""+name2+""" Labels</name>\n"""
kml.writelines(kmiddle)

print "Starting Label Loop..."

counter = 0
for iLine in ilist:

    # Increment counter
    counter += 1

    # Increment counter
    counter += 1

    if counter > 1:  # New Camera dat file has a system number header that allows chartsPic to see that it's an RCD30 camera
        # Parse the data in the Camera dat file
        mylist = iLine.strip().split(' ')
        mylist = [item for item in mylist if item]

        pid = mylist[0]
        fileName = mylist[1].split('.')[0]
        iName = os.path.join(fileName + '_scaled.jpeg')
        Lat = float(mylist[3])
        latF = format(Lat, '.11f')
        Lon = float(mylist[2]) #- 360  # RCD30 65025 Sensor Head and FramePro being 3rd party we have to compensate for longitude being incorrect in an older version of FramePro
        lonF = format(Lon, '.11f')
        zed = float(mylist[4])
        zedF = format(zed, '.4f')
        pitch = float(mylist[6])
        pitchF = format(pitch, '.13f')
        roll = float(mylist[5])
        rollF = format(roll, '.13f')
        heading = float(mylist[7])
        headingF = format(heading, '.13f')
        gpsSeconds = float(mylist[8]) + 0  # Compensating for the GPS/UTC offset set to zero if not needed; we compensate for this in Ipas CO+ later on
        gpsSecondsF = format(gpsSeconds, '.5f')
        picTime = getPictureTime(year, month, day, gpsSeconds, prev_time)
        prev_time = picTime

        # Convert Lat and Lon to radians
        Latrad = radians(Lat)
        Lonrad = radians(Lon)

        # Convert Lat and Lon to meters
        X = (Radius * (cos(Latrad))) * Lonrad
        Y = Radius * Latrad

        # Calculate pixel size based on flying height
        FH=zed
        PixSz=(FH*CCD_XY)/FL

        # Calculate pixel size in degrees for X and Y diminsions
        PixSzY = (degrees(PixSz/Radius))# * 1.10 WHAT WAS THIS FOR?????
        PixSzYneg = 1.00 * (degrees(PixSz/Radius))
        PixSzX = degrees(PixSz/(Radius * (cos(Latrad))))

        # Convert degress to radians (using * !DTOR <pi/180 ~= 0.01745>) ****Note H2 is set above******
        Prad = radians(pitch + BS_P)
        Rrad = radians(roll + BS_R)
        Hrad = radians(heading + BS_H)

        # Calculate s_inv
        s_inv = 1/(FL/FH)

        # Create terms for the M matrix
        M11 = cos(Prad)*sin(Hrad)
        M12 = -cos(Hrad)*cos(Rrad)-sin(Hrad)*sin(Prad)*sin(Rrad)
        M13 = cos(Hrad)*sin(Rrad)-sin(Hrad)*sin(Prad)*cos(Rrad)
        M21 = cos(Prad)*cos(Hrad)
        M22 = sin(Hrad)*cos(Rrad)-(cos(Hrad)*sin(Prad)*sin(Rrad))
        M23 = (-sin(Hrad)*sin(Rrad))-(cos(Hrad)*sin(Prad)*cos(Rrad))
        M31 = sin(Prad)
        M32 = cos(Prad)*sin(Rrad)
        M33 = cos(Prad)*cos(Rrad)

        # Define p matrix using PP offsets (image center) (rotate to +X direction of flight along track, +Y left wing across track, -FL)
        Xi = PP_Y
        Yi = -1.00 * PP_X
        FLneg = -1 * FL

        CP_X = (s_inv *(M11* Xi + M12 * Yi + M13 * FLneg)) + X
        CP_Y = (s_inv *(M21* Xi + M22 * Yi + M23 * FLneg)) + Y
        CP_Z = (s_inv *(M31* Xi + M32 * Yi + M33 * FLneg)) + FH

        # Calculate Upper left corner (from center) in mapping space (DIR FLT = +Y, Right Wing = +X), rotate, apply to center coords in mapping space
        ULX = CP_X  - (PixSz * PP_Pix_X)
        ULY = (PixSz * PP_Pix_Y) + CP_Y
        LRX = CP_X - (PixSz * PP_Pix_X)
        LRY = CP_Y - (PixSz * PP_Pix_Y)

        # Convert CP_X and CP_Y to Degrees Lat and - Long
        # East and West appear switched but it is the way X and Y
        # are handeled in the image reference frame above
        ULXLon = (degrees(ULX/(Radius * cos(Latrad)))) #- 360
        ULYLat = (degrees(ULY/Radius))
        LRXLon = (degrees(LRX/(Radius * cos(Latrad)))) #- 360
        LRYLat = (degrees(LRY/Radius))

        CenLat = (degrees(CP_Y/Radius))
        CenLon = (degrees(CP_X/(Radius * cos(Latrad))))

        # Convert center Lat, Long to UTM
        p = Proj(proj='utm',zone=zoneNum,ellps='WGS84')
        cenEast, cenNorth =  p(Lon,Lat)
        cenEastF = format(cenEast, '.11f')
        cenNorthF = format(cenNorth, '.11f')

        # Convert center Lat, Long to UTM
        p = Proj(proj='utm',zone=zoneNum,ellps='WGS84')
        ulE,  ulN =  p(ULXLon, ULYLat)

        # Use rotation to get params for 0 to 180 Degrees of heading
        Rot = 0 - heading
        ulEp = cenEast + ((ulE - cenEast) * cos(radians(Rot)) - (((ulN - cenNorth)) * sin(radians(Rot))))
        ulNp = cenNorth + ((((ulE - cenEast)) * sin(radians(Rot))) + (((ulN - cenNorth)) * cos(radians(Rot))))

        Easting = ulEp
        Northing = ulNp

        # Calculate the center of the upper left pixel
        cenULEst = cenEast - (PP_Pix_Y * PixSz)
        cenULNrt = cenNorth + ((PP_Pix_X * PixSz)*2)

        # Calculate Rotation
        Rotation = 0
        if imgtype == "C" :
            Rot = heading
            #print "The Rotation for the nav file is: " + str(Rot)
            if Rot > 0 and Rot < 180:
                Rotation = Rot
                #print "Rotation is from 0 to 180: " + str(Rotation)
                # Calculate Rotation for pixels of upper left for tfw
                PixSzNeg = -1 * PixSz
                lineA = PixSz * math.cos((pi/180)* Rotation)
                lineD = PixSzNeg * math.sin((pi/180)* Rotation)
                lineB = PixSzNeg * math.sin((pi/180)* Rotation)
                lineE = PixSzNeg * math.cos((pi/180)* Rotation)

            else:
                Rot = 360 + heading
                #print "The Correct Rotation for the nav file is: " + str(Rot)
                Rotation = Rot
                # Calculate Rotation for pixels of upper left for tfw
                PixSzNeg = -1 * PixSz
                lineA = PixSz * math.cos((pi/180)* Rotation)
                lineD = PixSzNeg * math.sin((pi/180)* Rotation)
                lineB = PixSzNeg * math.sin((pi/180)* Rotation)
                lineE = PixSzNeg * math.cos((pi/180)* Rotation)

        if imgtype == "R" :
            Rot = heading + 180.0
            if Rot > 360 : Rot = Rot -360
            if Rot < 180 : Rotation = 360 - Rot
            if Rot >= 180 : Rotation = -1 * (Rot * 1)

        # Calculate the clip
        nsClip = (North - South) * clip
        ewClip = (West - East) * clip

        # Write to the master KML
        kbody2 = """  	<Placemark>
        		<visibility>0</visibility>
        		<name>"""+iName+"""</name>
        		<styleUrl>#FEATURES_LABELS</styleUrl>
        		<Point>
        			<extrude>0</extrude>
        			<altitudeMode>absolute</altitudeMode>
        			<coordinates>"""+str(CenLon)+""","""+str(CenLat)+""",0</coordinates>
        		</Point>
        		</Placemark>\n"""
        kml.writelines(kbody2)

        # Contructs the string list for use in the Original Camera Sync file associated with HF and
        # the RCD30 Camera Sync file with that same formatting; 0 file can be used in
        camLines0 = (' %-20s  %60s  %-13s  %-13s  %-10s  -1  -1  -1  %s  %s  %-14s  %-15s  %-13s  %16s  %16s  %-14s  \n')%\
        (pid, iName, cenEastF, cenNorthF, zedF, zoneNum, zoneHem, latF, lonF, gpsSecondsF, rollF, pitchF, headingF)
        camLinesR = (' %-20s  %60s  %-13s  %-13s  %-10s  -1  -1  -1  %s  %s  %-14s  %-15s  %-13s  %16s  %16s  %-14s  %-16s  \n')%\
        (pid, iName, cenEastF, cenNorthF, zedF, zoneNum, zoneHem, latF, lonF, gpsSecondsF, rollF, pitchF, headingF, picTime)

        # Write the new strings to the new file
        cameraSync0.writelines(camLines0)
        cameraSyncR.writelines(camLinesR)


kfoot = """</Folder>
</Document>
</kml>"""
kml.writelines(kfoot)

kml.flush()
kml.close()
cameraSync0.flush()
cameraSyncR.flush()
cameraSync0.close()
cameraSyncR.close()

kmzName = os.path.join(cwd+"\\"+name2+"_thumbs.kmz")
kmz = zipfile.ZipFile(kmzName, "w")

if os.name == "nt":
    for name in glob.glob("*scaled.jpeg"):
        kmz.write(name, os.path.basename(name), zipfile.ZIP_DEFLATED)
        #print name
    for name in glob.glob("*.kml"):
        kmz.write(name, os.path.basename(name), zipfile.ZIP_DEFLATED)
        #print name

kmz.close()


import time
sleepsec = 1
print "Finished, closing in:"
print "1 Seconds"
time.sleep(sleepsec)

