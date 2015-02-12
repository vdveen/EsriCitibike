#This code is a test to look for some initial patterns in the data.

opendata = open('data/Citibike-2.csv')  #Open and read file
lines = opendata.read()
line = lines.split(',')

count = 0             #Prereq definitions for the loop below
trip = []
gender = []


for item in line:         #Getting the relevant values
  count = count + 1
  if count <= 306000:
    if count % 9 == 1 or count % 9 == 0:   #Gender or tripduration
      if 'd' in item:               #Making sure header is ignored
        item = item
      elif len(item) == 1:      #Adding the gender to the list
        gender.append(int(item))
      else:
        item = item[2:-1]       #Adding and slicing tripduration from '"\n 404"' to 404
        trip.append(int(item))

#Now that gender and trip list are filled, this function zips them together
dictionary = zip(trip, gender)

#Now lets separate the male and female values
#and put them in a new list
maletrip = []
femaletrip = []

for value in dictionary:
    if value[1] == 1:
      maletrip.append(int(value[0]))

for value in dictionary:
    if value[1] == 2:
      femaletrip.append(int(value[0]))

print 'The Average for males is:', sum(maletrip) / len(maletrip)
print 'The Average for females is:', sum(femaletrip) / len(femaletrip)
