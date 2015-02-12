import arcpy
from sys import exit

#Set workspace and define layer input file
arcpy.env.workspace = 'Data/Output.gdb'
layerfile = arcpy.mapping.Layer('output.lyr')

#The layer object is the first obj in the layers list, hence [0]
layer = arcpy.mapping.ListLayers(layerfile)[0]
print layer.name

#Make a list of the time numbers for each interval for the entire day
timelist = []
interval = 10
time = 0
endtime = 1400
while time < endtime:
    time += interval
    timelist.append(time)
print timelist

#Generate layer file that displays all the trips
#that are occuring during a certain time moment
layerslist = []
for time in timelist:
    #Create definition query that selects the trips
    layer.definitionQuery = '"StartNumber" < ' + str(time) + \
    ' AND "EndNumber" > ' + str(time)
    copyname = 'timelayers/time' + str(time)
    #Save this layer file
    layer.saveACopy(copyname)
    copyname += '.lyr'
    copyname = copyname[11:]
    #Add the layer file to a list to refer to later
    layerslist.append(copyname)

#Change workspace to find new map document
arcpy.env.workspace = 'timelayers/'
mxd = arcpy.mapping.MapDocument('timelayers/Scratch.mxd')
df = arcpy.mapping.ListDataFrames(mxd)[0]

count = 0
for item in layerslist:
    #Add layer from the list and render an image
    addlayer = arcpy.mapping.Layer(item)
    arcpy.mapping.AddLayer(df,addlayer)
    count += 1
    bgc = '225,225,225'
    frame = 'frames/frame' + str(count) + '.png'
    arcpy.mapping.ExportToPNG(mxd, frame, df, 1920, 1080, \
    color_mode = '8-BIT_GRAYSCALE', background_color = bgc)

    #Remove all layers, just to be sure
    for lyr in arcpy.mapping.ListLayers(mxd, "*",df):
        arcpy.mapping.RemoveLayer(df, lyr)
    print frame

mxd.save()
exit()

