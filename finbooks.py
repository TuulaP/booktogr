#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Book data from finna by isbn

from urllib import urlopen
import pprint
import simplejson as json
# from booktogr import chkGoodReads
import sys

from kitchen.text.converters import getwriter

url = "https://api.finna.fi/v1/search?lookfor="
CSVSEP = ";"
QUOTE = '"'
full = "&field[]=fullRecord"
recordurl = "https://api.finna.fi/v1/record?id="
suffix = "&field[]=id"


def parseFEmail(emailstr):
    # print("F.email found: ", emailstr)
    bookids = []
    lineid = 0  # every evem line has ids.
    alku = 1
    alkub = 0
    osuus = emailstr.split("Lainat")[1]
    # print("xxxx - osuus", osuus)

    for line in osuus.split("\r\n"):  # emailstr.split("\r\n"):
        # if "primal" in line:
        # print("xxx {0} : {1}".format(lineid, line))
        words = line.split(" ")

        if lineid == 1:
            alku = 1

        if "Teoksia yhteens" in line:
            break

        if alku:
            if lineid % 2 == 0:  # viivakoodi -> ei voi hakea ; name
                # print("Processing: ", words[0])
                pass
            else:
                bookid = line + "*"
                if (len(bookid) > 3):
                    # pass
                    # print("sss")
                    print("bookid", bookid)

                    isbn = getFinnaRecord(seekFinnabyName(bookid))
                    bookids.append(isbn)
                    isbn = ""
                    bookid = ""
        lineid += 1

    print("Books found:", bookids)
    return bookids


def seekFinnabyName(bookname):

    result = urlopen(url+bookname+suffix).read()
    result = json.loads(result)
    result = result.get('records')

    # print "data searched:" + url + isbn + "\n"
    pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(result)

    resultSet = result[0]

    print result[0]['id']

    return result[0]['id']


def getFinnaRecord(bookid):
    result = urlopen(recordurl+bookid+full).read()
    result = json.loads(result)
    result = result.get('records')

    print ">>", bookid, "\n"

    xmlmarc = result[0]['fullRecord']

    # pp = pprint.PrettyPrinter(indent=4)
    with open("kirja.xml", "w") as text_file:
        text_file.write(xmlmarc.encode("UTF-8"))

    from pymarc import parse_xml_to_array
    reader = parse_xml_to_array("kirja.xml")

    details = {}

    import re
    isbn = ""
    isbns = []

    for record in reader:

        for f in record.get_fields('020'):
            #print("kentta:", f['a'])
            isbns.append(f['a'].replace("-", ""))

        try:
            isbn = record['020']['a']
        except TypeError:
            pass

    if (len(isbns) > 1):
        if (len(isbns[0]) > len(isbns[1])):
            isbn = isbns[0]

        if (len(isbns[1]) > len(isbns[0])):
            isbn = isbns[1]

    #print("Valittu ISBN: {0}".format(isbn))

    return isbn.replace("-", "")


# ysid = seekFinnabyName(
#    "Rocket surgery made easy : the do-it-yourself guide to findi*")

# "Primal leadership : unleashing the power of emotional intell*")

#isbn = getFinnaRecord(ysid)
#print("ISBN: ", isbn)
