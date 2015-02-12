#Code written by vdveen
#Purpose: cleaning up the original data.
#So the original csv file has a million apostrophes, which I
#first need to get rid of.

opendata = open('data/2014-07 - Citi Bike trip data.csv')  #Open and read file
rawdata = opendata.read()
rawdata = rawdata.replace('\r', ',')  #Replace newlines with commas
rawdata = rawdata.split(',')       #Then split on commas

#New list to add to
bikedata = []
count = 0

#Check all items in data, remove brackets, convert it into a flawless file.
for item in rawdata:
  if 'N' in item:                         #Eliminating \N values, that are null anyway
    item = 'null'
    bikedata.append(item)

  elif item.startswith('"'):      #All values get their " " cut off
    item = item[1:-1]
    bikedata.append(item)

  elif count % 16 == 0:           #The first items in the line don't need to do that
    bikedata.append(item)

opendata.close()
print 'Cleaned up data'

#Here, the original data is fully cleaned up.
#This part of the script creates a file for the cleaned up data.
bikefile = open('data/Citibike-clean.csv', 'w')
for item in bikedata:
  bikefile.write(item)
  bikefile.write(',')
bikefile.close()

#So, done cleaning, now we create a new file to put the
#relevant data in, stripping out all unnecessary stuff.
newfile = open('data/Citibike-2.csv', 'w')
count = 0

#Now, lets remove the unneeded columns
for item in bikedata:
  count = count + 1           #Counts what number the item is
  if count % 15 == 4:           #Don't write start station ID
    newfile.write('')
  elif count % 15 == 5:         #Don't write start station name
    newfile.write('')
  elif count % 15 == 8:         #Don't write end station ID
    newfile.write('')
  elif count % 15 == 9:         #Don't write end station name
    newfile.write('')
  elif count % 15 == 9:         #Don't write end station name
      newfile.write('')
  elif count % 15 == 12:        #Don't write bike ID
      newfile.write('')
  elif count % 15 == 13:        #Don't write subscriber type
    newfile.write('')
  else:                         #Write everything else
    newfile.write(item)
    newfile.write(',')


#Finally, the file is how we want it. Let's save it to the file!
newfile.close()
print 'Done aaand...done.'
