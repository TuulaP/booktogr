
# save to csv

import unicodecsv as csv

def writeToCSV (filename, row):

  #from io import BytesIO
  #f = BytesIO()
  with open (filename, 'ab') as csvf:
    w = csv.writer(csvf, encoding='utf-8',delimiter=',')
    w.writerow(row)



#a=1
#b=2
#c=3
#d=4
#writeToCSV("koe3.csv", (a,b,c,d))
#print(aaa)


