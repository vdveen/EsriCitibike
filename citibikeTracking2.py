#TAKE 2: Now attempting full Tracking Analyst support
#Script to get from Citibike data to a geodatabase with the needed trip data.
#
#Get start and end point
#Give them datetime and

import arcpy
import datetime
from sys import exit
arcpy.env.overwriteOutput = True

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
InputFile = 'data/2014-07 - Citi Bike trip data.csv'
fields = ['starttime', 'start station latitude', 'start station longitude',\
 'end station latitude', 'end station longitude', 'stoptime']
cursor = arcpy.da.SearchCursor(InputFile, fields)

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
    if count % 100:
        print 'Count: ' + str(count)

    #End at 7am as test sample
    if startdate.hour == 3:
        print 'Total Count: ' + str(count)
        break

del cursor, inscursor, row

print 'Done now'