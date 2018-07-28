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
    ##print(result)
    # <input type="hidden" name="bib" value="2969867">
    #>> m = re.search('(?<=-)\w+', 'spam-egg')
    #>>> m.group(0)
    #'egg'
    m = re.search('(.*name="bib" value=")(\w+)' , result)
    res = m.group(2)
    ##print("*** bookemailid: {0} --> bookcode: {1}".format(bookcode, res))

    return res


def seekKohaMarc(bookcode):
  url = base + "/opac-MARCdetail.pl?biblionumber=" 

  result = urlopen(url+bookcode).read()

  #grab from page the isbn part from MARC
  aa = result.split('International Standard Book Number')[1]
  bb = aa.split('040 ## - Luetteloiva')[0]
  
  # and finally the isbn
  m = re.search('<td>(\d+).*</td>', bb)
  res = m.group(1)
  ##print("*** Koha id: {0} --> ISBN: {1}".format(bookcode, res))
  return res


def parseKohaEmail (emailstr):
  ##print("Input: ", emailstr)
  if (len(emailstr)==0):
    return []

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





##id   = seekKohaSearch("49120180709218")
##isbn = seekKohaMarc(id)
