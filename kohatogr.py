#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Book data a koha library web system based on book id got from email

from urllib import urlopen
import pprint
import simplejson as json
import codecs
import sys

from kitchen.text.converters import getwriter
UTF8Writer = getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

from kitchen.text.converters import getwriter, to_bytes, to_unicode
import re

base= "https://www.lumme-kirjastot.fi/cgi-bin/koha"
url= base+"/opac-search.pl?idx=&q="
suffix ="+&branch_group_limit="

def seekKohaSearch(bookcode):

    result = urlopen(url+bookcode+suffix).read()
    print(url+bookcode+suffix)
    ##print(result)
    # <input type="hidden" name="bib" value="2969867">
    #>> m = re.search('(?<=-)\w+', 'spam-egg')
    #>>> m.group(0)
    #'egg'
    m = re.search('(.*name="bib" value=")(\w+)' , result)
    tul = m.group(2)
    #print("!!!", tul)
    return tul


def seekKohaMarc(bookcode):
  url = base + "/opac-MARCdetail.pl?biblionumber=" 

  result = urlopen(url+bookcode).read()

  #grab from page the isbn part from MARC
  aa = result.split('International Standard Book Number')[1]
  bb = aa.split('040 ## - Luetteloiva')[0]
  
  # and finally the isbn
  m = re.search('<td>(\d+).*?</td>', bb)
  res = m.group(1)

  print("*** Koha id: {0} --> ISBN: {1}".format(bookcode, res))
  if (len(res)<9):
    print("ERR: issue with getting proper id for {0} RAW:{1}".format(bookcode,bb))
    sys.exit(1)
  
  return res


def parseKohaEmail (emailstr):
  print("email found: ", emailstr)
  kohaids = []
  lineid = 0 # every evem line has ids.

  for line in emailstr.split("\n"):
    words = line.split(" ")
    if lineid % 2 != 0:
      ##print("Processing: ", words[0] )
      pass
    else:
      kohaid = words[0]
      if (len(kohaid)>3):
        #print("kohaid", kohaid)
        kohaids.append(seekKohaMarc(seekKohaSearch(kohaid)))
    lineid+=1

  print("Books found:",kohaids)
  return kohaids


def giveBookDetails(bookcode, isbn):
  url = base + "/opac-MARCdetail.pl?biblionumber=" 

  print(url)
  bookcode = seekKohaSearch(isbn)
  print(bookcode)

  result = urlopen(url+bookcode).read()

  #  #Need: at minimum: title, author, publisher, year published

  # TODO: Cleanup & regexify

  #grab from page the isbn part from MARC
  aa = result.split('International Standard Book Number')[1]
  bb = aa.split('040 ## - Luetteloiva')[0]

  # and finally the isbn
  m = re.search('<td>(\d+).*?</td>', bb)
  res = m.group(1)

  #grab from page the isbn part from MARC
  aa = result.split('245 10 - Nimeke- ja vastuullisuusmerkintö')[1]
  bb = aa.split('Päänimeke')[1]
  m = re.search('<td>(.*?)\ \/</td>', bb)
  title = m.group(1)
  #print("Title:", title)

  bb = aa.split("Vastuullisuusmerkinnöt jne.")[1]
  m = re.search('<td>(.*?)\.</td>', bb)
  author = m.group(1)
  #print("Author:", author)

  aa = result.split("Julkaisijan/kustantajan, jakajan jne. nimi")[1]
  m = re.search('<td>(.+)\,</td>', aa)
  publisher = m.group(1)
  #print("Publisher:",publisher)

  aa = result.split("Julkaisu-, jakelu- jne. aika")[1]
  m = re.search('<td>(\d+?)\.</td>', bb)
  pubyear = m.group(1)
  #print("Pubyear:", pubyear)

  return (title, author, isbn, publisher, pubyear)



##id   = seekKohaSearch("49120180709218")
##isbn = seekKohaMarc(id)

#isbn = "9789525132977"
#id = seekKohaSearch(isbn)
#print(id)

#aaa= giveBookdetails(id, isbn)
#bookdets = (aaa[0],aaa[1],aaa[2],"","",aaa[3],"",aaa[4])
#print ("Kirja:", bookdets)

##print("!",aaa[3])


#from tpcsvutils import writeToCSV

#Title, Author, ISBN, My Rating, Average Rating, Publisher, Binding, Year Published, Original Publication Year,
#writeToCSV('koe2.csv', bookdets)





