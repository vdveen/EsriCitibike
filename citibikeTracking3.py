#TAKE 2: Now attempting full Tracking Analyst support
#Script to get from Citibike data to a geodatabase with the needed trip data.

#PART ONE: Getting lines & points with useful data attatched to them
#Read raw Citibike data with a Search Cursor, and insert the resulting
#point info into an empty feature class. Then, use the Tracking Analyst
#to get speed, distance & direction from points to a line feature.

import arcpy
import datetime
from sys import exit
arcpy.env.overwriteOutput = True

#Warning if TA isn't available
if arcpy.CheckOutExtension('Tracking') == 'CheckedOut':
    pass
else:
    exit('Tracking Analyst License not available')

#Define spatial reference
sr = arcpy.SpatialReference(4326)
arcpy.env.outputCoordinateSystem = sr #just to be sure

#Create new database to put fc in
try:
    arcpy.CreateFileGDB_management("Data", "Tracking.gdb")
except:
    pass
outgdb = 'Data/Tracking.gdb'
arcpy.env.workspace = outgdb

#Get file and create search cursor from it
inputfile = 'data/2014-07 - Citi Bike trip data.csv'
fields = ['starttime', 'start station latitude', 'start station longitude',\
 'end station latitude', 'end station longitude', 'stoptime']
cursor = arcpy.da.SearchCursor(inputfile, fields)

#Create fc to populate
filename = 'Points'
arcpy.CreateFeatureclass_management(outgdb, filename, \
'POINT', None, 'DISABLED', 'DISABLED', sr)
pointfc = 'Data/Tracking.gdb/Points'

#Add date to that fc
arcpy.AddField_management(pointfc, 'Time', 'DATE')
arcpy.AddField_management(pointfc, 'TrackID', 'FLOAT')

#Make insert cursor for that fc
fields2 = ['SHAPE@','Time', 'TrackID']
inscursor = arcpy.da.InsertCursor(pointfc, fields2)

#Loop through rows of source data, generate points and fill the new pointfc
count = 0

for row in cursor:
    count += 1
    #get the coordinates of the start and end
    startLat = row[1] #start station latitude
    startLon = row[2] #start station longitude
    endLat = row[3] #end station latitude
    endLon = row[4] #end station longitude

    #make two points in Arcpy
    start = arcpy.Point(startLon,startLat,None,None,0)
    end = arcpy.Point(endLon,endLat,None,None,1)

    #Retrieve the start and end hour datetime
    startdate = row[0]
    enddate = row[5]

    #Add two new rows to Points fc with the data
    inscursor.insertRow([start,startdate,count])
    inscursor.insertRow([end,enddate,count])

    #Counter
    if count % 100 == 0:
        print 'Count: ' + str(count)

    #End at 7am as test sample
    if startdate.hour == 1:
        print 'Total Count: ' + str(count)
        break

#Clear Curse of the Lock of the Cursor
del inscursor, cursor, row

#Put properties of trips to line features with Tracking Analyst
#Note: I probably could have interpolated directly, but doing this
#makes it easier to make other visualizations, e.g. speed and direction
filename = 'Lines'
arcpy.TrackIntervalsToLine_ta(pointfc,filename,"Time","TrackID","#",\
"01043-Dutch_(Netherlands)","#","#","KILOMETERS","Distance_KM_Time","MINUTES",\
"Duration_MIN_Time","KILOMETERS_PER_HOUR","Speed_KPH_Time","DEGREES",\
"Course_DEG_Time")


#PART 2: Drawing Lines
#From the points / line data, interpolate three points per trip (more if possible)
#Use a Search Cursor to read rows, and an Insert Cursor to add points to

#Make searchcursor from the line fc
inputfile = 'Data/Tracking.gdb/Lines'
fields = ['SHAPE@', 'Start_Time', 'End_Time', 'Duration_MIN_Time']
cursor = arcpy.da.SearchCursor(inputfile, fields)


#Create new fc to populate interpolated points
filename = 'Points2'
arcpy.CreateFeatureclass_management(outgdb, filename, \
'POINT', None, 'DISABLED', 'DISABLED', sr)
pointfc2 = 'Data/Tracking.gdb/Points2'

#Add fields to that fc
arcpy.AddField_management(pointfc2, 'Time', 'DATE')
arcpy.AddField_management(pointfc2, 'TrackID', 'FLOAT')

#Make insert cursor for that fc
fields2 = ['SHAPE@','Time', 'TrackID']
inscursor = arcpy.da.InsertCursor(pointfc2, fields2)

#Go through the search cursor, interpolate, and save to the new points fc
for row in cursor:
    lineobj = row[0]
    starttime = row[1]
    endtime = row[2]
    duration = row[3]


print 'Done now'