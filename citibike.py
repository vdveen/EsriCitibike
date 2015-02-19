#Script to get from Citibike data to a geodatabase with the needed trip data.

import arcpy
import datetime
from sys import exit
arcpy.env.overwriteOutput = True

#Get file and create search cursor from it
InputFile = 'data/2014-07 - Citi Bike trip data.csv'
fields = ['starttime', 'start station latitude', 'start station longitude',\
 'end station latitude', 'end station longitude', 'stoptime']
cursor = arcpy.SearchCursor(InputFile, fields)

#Create lists to be used later
fc = []
hr = []
hr2 = []
minutes = []
minutes2 = []
cutpoints = []
failcount = 0

for row in cursor:
    #get the coordinates of the start and end
    startLat = row.getValue('start station latitude')
    startLon = row.getValue('start station longitude')
    endLat = row.getValue('end station latitude')
    endLon = row.getValue('end station longitude')

    #make two points in Arcpy
    start = arcpy.Point(startLon,startLat,None,None,0)
    end = arcpy.Point(endLon,endLat,None,None,1)

    #Put them in an array
    triplineArray = arcpy.Array([start,end])

    #Create line between the two
    tripline = arcpy.Polyline(triplineArray)

    #Put them in a fc
    fc.append(tripline)

    #Try to find the midpoint and store it in a list
    try:
        midpoint = tripline.positionAlongLine(0.50, True)
        cutpoints.append(midpoint)
    except:
        failcount += 1
        print failcount

    #Put start hour in a list
    values = row.getValue('starttime'), #somehow that comma matters
    date = values[0]
    hour = date.hour
    hr.append(hour)

    #Put start minutes in a list too
    minute = date.minute
    print date, hour, minute
    minutes.append(minute)

    #Put end hour in a list
    values2 = row.getValue('stoptime'), #somehow that comma matters
    date2 = values2[0]
    hour2 = date2.hour
    hr2.append(hour2)

    #Put end minutes in a list too
    minute2 = date2.minute
    minutes2.append(minute2)

    #End at 7am
    if date.hour == 7:
        break

output = 'Data/Output.gdb/output'

#Create dataset to put fc in
try:
    arcpy.CreateFileGDB_management("Data", "Output.gdb")
except:
    'Error with creating GDB'

#Put the fc and midpoints in the dataset
arcpy.CopyFeatures_management(fc, output)
arcpy.CopyFeatures_management(cutpoints, 'Data/Output.gdb/outputPoints')

#Project the fc in the dataset
arcpy.DefineProjection_management(output, 32662)


arcpy.env.workspace = 'Data/Output.gdb'

#Add field to file with start hour and minute
arcpy.AddField_management('output', 'StartHour', 'FLOAT')
arcpy.AddField_management('output', 'StartMinute', 'FLOAT')

#Add field to file with end hour and minute
arcpy.AddField_management('output', 'EndHour', 'FLOAT')
arcpy.AddField_management('output', 'EndMinute', 'FLOAT')


#Run update cursor to fill it in
cursor2 = arcpy.UpdateCursor(output)
houriter = iter(hr)
hour2iter = iter(hr2)
miniter = iter(minutes)
min2iter = iter(minutes2)

count = 0

for row in cursor2:
    #Iterate through lists and rows and find values of iters
    row.StartHour = houriter.next()
    row.StartMinute = miniter.next()
    row.EndHour = hour2iter.next()
    row.EndMinute = min2iter.next()

    #Update row with new values and show progress
    cursor2.updateRow(row)
    count += 1
    if count % 100 == 0:
        print count

#Clean up mess
del cursor, cursor2, row

print 'Done now'