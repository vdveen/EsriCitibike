#In the same folder as this script, there should be a /Data folder with the .csv,
#and a /Data/Scratch folder for scratch data.

#Script to get from Citibike raw data to two ArcGIS Tracking layers of said trip data

#PART ONE: Getting lines & points with useful data attatched to them
#Read raw Citibike data with a Search Cursor, and insert the resulting
#point info into an empty point  feature class.

import arcpy
import datetime
from sys import exit
arcpy.env.overwriteOutput = True

#Warning if TA or NA isn't available
if arcpy.CheckOutExtension('Tracking') == 'CheckedOut':
    pass
else:
    exit('Tracking Analyst License not available')

if arcpy.CheckOutExtension('Network') == 'CheckedOut':
    pass
else:
    exit('Network Analyst License not available')

#Define spatial reference
sr = arcpy.SpatialReference(4326)
arcpy.env.outputCoordinateSystem = sr #just to be sure

#Create new file geodatabase to put fc in
try:
    arcpy.CreateFileGDB_management('Data', 'Tracking.gdb')
except:
    pass
outgdb = 'Data/Tracking.gdb'
arcpy.env.workspace = outgdb

#Get Citibike file and create search cursor from it
inputfile = 'data/2014-07 - Citi Bike trip data.csv'
fields = ['starttime', 'start station latitude', 'start station longitude',\
 'end station latitude', 'end station longitude', 'stoptime']
cursor = arcpy.da.SearchCursor(inputfile, fields)

#Create fc to populate
filename = 'Points'
arcpy.CreateFeatureclass_management(outgdb, filename, \
'POINT', None, 'DISABLED', 'DISABLED', sr)
pointfc = 'Data/Tracking.gdb/Points'

#Add date to the fc
arcpy.AddField_management(pointfc, 'Time', 'DATE')
arcpy.AddField_management(pointfc, 'TrackID', 'FLOAT')

#Make insert cursor for the fc
fields2 = ['SHAPE@','Time', 'TrackID']
inscursor = arcpy.da.InsertCursor(pointfc, fields2)


#Loop through rows of source data, generate points and fill the new pointfc
totalcount = 0

for row in cursor:

    #get the coordinates of the start and end
    startLat = row[1] #start station latitude
    startLon = row[2] #start station longitude
    endLat = row[3] #end station latitude
    endLon = row[4] #end station longitude

    #Retrieve the start and end hour datetime
    startdate = row[0]
    enddate = row[5]

    #Start at an hour
    if startdate.minute == 2:
        totalcount += 1

        #make two points in Arcpy
        start = arcpy.Point(startLon,startLat,None,None,0)
        end = arcpy.Point(endLon,endLat,None,None,1)

        #Add two new rows to Points fc with the data
        inscursor.insertRow([start,startdate,totalcount])
        inscursor.insertRow([end,enddate,totalcount])

        #Counter
        if totalcount % 100 == 0:
            print 'Count: ' + str(totalcount)

    #End at an hour
    elif startdate.minute == 8:
        print 'Total Count: ' + str(totalcount)
        break

del inscursor, cursor, row

print 'Part 1/4 Complete'
#PART TWO: Use the points fc and the track ID to generate shortest route paths
#from start- to end location using the Network Analyst and a Route Layer.
#First, preparations to make the for loops work:

#Start with network file of Manhattan and Brooklyn
nycND = 'Data/NYC/RoadsManhattanBrooklyn_ND.nd'

#Make route layer
RouteLayer = arcpy.na.MakeRouteLayer(nycND,'Route Layer', 'Length',\
'USE_INPUT_ORDER','PRESERVE_BOTH','NO_TIMEWINDOWS','#','ALLOW_UTURNS','#',\
'NO_HIERARCHY','#','TRUE_LINES_WITH_MEASURES','#')

#Get the layer object so it can be used as an object later on
RouteLayer = RouteLayer.getOutput(0)

#Get the names of all the sublayers within the route layer.
subLayerNames = arcpy.na.GetNAClassNames(RouteLayer)

#Stores the stop name so we can use it in the AddPoints function
stops = subLayerNames['Stops']

#Make a range for every trackID, so from 1 to n(TrackID)
numberList = range(1,(totalcount+1))
nameList = []

#Select the two points belonging to each trip using the trackID
#Output: list of shapefiles containing two points, with the trackID in the name of the shp
pointcount = 0
for number in numberList:
    pointcount += 1
    query = '"TrackID" = ' + str(number) #selecting for the track ID
    name = 'Points' + str(number)
    nameList.append(name)
    arcpy.Select_analysis(pointfc, name, query)
    if pointcount % 10 == 0:
        print pointcount, 'Trip Points Generated'

#Just a check to see if the last name in the list has the same number as the total count
print 'Final: ', nameList[-1:]

#Now, go through the list of .shps
routecount = 0
for name in nameList:
    routecount += 1
    #Add locations from the gdb because the Select shapefiles are stored there
    nameprefix = 'Data/Tracking.gdb/'
    name2 = nameprefix + name
    print name2
    arcpy.na.AddLocations(RouteLayer, stops, name2, '', '500 Meters', append = 'CLEAR')

    #Solve. Skip is selected so it will continue if it can't find a path.
    try:
        arcpy.na.Solve(RouteLayer, 'SKIP')
    except:
        pass

    #Save .lyrs in the scratch folder
    nameprefix = 'Data/Scratch/'
    name2 = nameprefix + name
    arcpy.management.SaveToLayerFile(RouteLayer, name2,'RELATIVE')
    if pointcount % 10 == 0:
        print pointcount, 'Routes Generated'

#Change workspace to the scratch folder
arcpy.env.workspace = 'Data/Scratch'

#Create new file geodatabase to put fc in
try:
    arcpy.CreateFileGDB_management('Data/Scratch', 'Lines.gdb')
except:
    pass

#Find all the lyr files in the scratch folder and loop through them
lyrlist = arcpy.ListFiles('*.lyr')

for lyr in lyrlist:
    #Make layer objects out of the current .lyr in the list
    lyrpath = 'Data/Scratch/' + str(lyr)
    layer = arcpy.mapping.Layer(lyrpath)

    #Find the route layer inside the .lyr
    route = arcpy.mapping.ListLayers(layer)[3]

    #Copy the route to a new fc
    name2 = 'Lines.gdb/Polyline' + lyr[:-4]
    arcpy.management.CopyFeatures(route, name2)
    arcpy.management.Delete(lyr)
    print route, name2

print 'Part 2/4 Complete'
#PART THREE: Take the new fc's and add the time information to them
#This is because the route layer stuff throws all other data away

#Get the time data in one fc
arcpy.env.workspace = 'Data/Tracking.gdb'
pointlist = arcpy.ListFeatureClasses()
arcpy.management.Merge(pointlist,'MergedPoints')
print 'Merged'

#Change workspace to the lines database folder
arcpy.env.workspace = 'Data/Scratch/Lines.gdb'

#List the polyline shapefiles
shplist = arcpy.ListFeatureClasses('Poly*')
print shplist

#Add fields to the PolylinePoints
for fc in shplist:
    #Add fields to the fc
    arcpy.AddField_management(fc, 'StartTime', 'DATE')
    arcpy.AddField_management(fc, 'EndTime', 'DATE')
    arcpy.AddField_management(fc, 'TrackID', 'FLOAT')

    #Fill the TrackID field
    trackID = fc[14:]
    arcpy.management.CalculateField(fc,'TrackID', trackID)

#Merge the PolylinePoints together
arcpy.management.Merge(shplist,'MergedLines')

#Make a search cursor from that merged points fc
fields = ['OID@', 'TrackID', 'Time']
cursor = arcpy.da.SearchCursor('Data/Tracking.gdb/MergedPoints', fields)

#Make an update cursor for the PolylinePoints
fields2 = ['OID@', 'StartTime', 'EndTime', 'TrackID']
upcursor = arcpy.da.UpdateCursor('Data/Scratch/Lines.gdb/MergedLines', fields2)

#Add time fields

for uprow in upcursor:
    #Loop through the triplines that need the times added to them
    linetrackID = uprow[3]
    for row in cursor:
        #Now loop through the search cursor to find the accompanying times
        pointstrackID = row[1]

        #If the row's trackID number equals the lines' trackID
        if linetrackID == row[1]:
            #Compare it to the OID to see if it is the start or the end time
            if float(row[0]) - 2*row[1] == -1:
                #Starttime has an OID of half the track ID -1.
                uprow[1] = row[2]
                upcursor.updateRow(uprow)
            elif float(row[0]) % row[1] == 0:
                #Endtime's OID is just half of the track ID
                uprow[2] = row[2]
                upcursor.updateRow(uprow)
    #Reset cursor so the next tripline can loop through it again
    cursor.reset()
    if linetrackID % 50 == 0:
        print 'Lines tracked: ', linetrackID


print 'Part 3/4 Complete'
#PART 4: Drawing Lines
#From the points / line data, interpolate a point every 100 m
#Use a Search Cursor to read rows, and an Insert Cursor to add points to

#Make searchcursor from the line fc
inputfile = 'Data/Scratch/Lines.gdb/MergedLines'
fields = ['SHAPE@', 'StartTime', 'EndTime', 'TrackID']
cursor = arcpy.da.SearchCursor(inputfile, fields)

#Create new fc to populate interpolated points
try:
    filename = 'Interpoints'
    outgdb = 'Data/Scratch/Lines.gdb'
    arcpy.CreateFeatureclass_management(outgdb, filename, \
    'POINT', None, 'DISABLED', 'DISABLED', sr)
except:
    pass

pointfc2 = 'Data/Scratch/Lines.gdb/Interpoints'

#Add fields to that fc
arcpy.AddField_management(pointfc2, 'Time', 'DATE')
arcpy.AddField_management(pointfc2, 'TrackID', 'FLOAT')

#Make insert cursor for that fc
fields2 = ['SHAPE@','Time', 'TrackID']
inscursor = arcpy.da.InsertCursor(pointfc2, fields2)

#Make an update cursor for the PolylinePoints
fields2 = ['SHAPE@', 'StartTime', 'EndTime', 'TrackID']
linecursor = arcpy.da.SearchCursor('Data/Scratch/Lines.gdb/MergedLines', fields2)

#The distance interval of the new points on the trip line
splitDistance = 0.001

trackID = 0

#Function to take that distance and interpolate points with the row information
def Interpolator3000(lineobj,starttime,endtime):
    #Total and current length
    length = lineobj.length
    currentLength = 0
    global trackID
    trackID += 1

    whilecounter = 1
    #Make a point every ~100m and interpolate the time
    while currentLength < length:

        #Make point along line
        percentageOfLine = (currentLength / length)
        point = lineobj.positionAlongLine(percentageOfLine,'True')

        #Get time of that point
        timedelta = endtime - starttime
        pointtime = starttime + ((timedelta * int(percentageOfLine*1000))/1000)

        #Insert row and update the trackID and length counters
        inscursor.insertRow([point, pointtime, trackID])
        currentLength += splitDistance
        whilecounter += 1
        if whilecounter % 100 == 0:
            print 'Interpolated ' + whilecounter + 'points'

    #Insert the last point
    inscursor.insertRow([lineobj.lastPoint,endtime,trackID])


#Go through the search cursor, interpolate, and save to the new points fc
for row in linecursor:
    #Get info from cursor row
    lineobj = row[0]
    starttime = row[1]
    endtime = row[2]

    try:
        #Add the interpolated points with the function
        Interpolator3000(lineobj,starttime,endtime)
    except:
        pass
del inscursor,cursor


#Make two tracking layers
mergedlines = 'Data/Scratch/Lines.gdb/MergedLines'
arcpy.MakeTrackingLayer_ta(mergedlines,"MergedLines_Layer","NO_TIME_ZONE","ADJUSTED_FOR_DST","KEEP_ON_DISK","StartTime","#","01043-Dutch_(Netherlands)","#","#","TrackID")

interpoints = 'Data/Scratch/Lines.gdb/InterPoints'
arcpy.MakeTrackingLayer_ta(interpoints,"Interpoints_Layer","NO_TIME_ZONE","ADJUSTED_FOR_DST","KEEP_ON_DISK","Time","#","01043-Dutch_(Netherlands)","#","#","TrackID")
print 'Part 4/4 Complete'

exit('')
