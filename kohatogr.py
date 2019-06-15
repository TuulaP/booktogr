#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Book data a koha library web system based on book id got from email

import re
from kitchen.text.converters import getwriter, to_bytes, to_unicode
from urllib import urlopen
import pprint
import simplejson as json
import codecs
import sys
from finbooks import seekFinnabyName, getFinnaRecord

from kitchen.text.converters import getwriter
UTF8Writer = getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)


base = "https://www.lumme-kirjastot.fi/cgi-bin/koha"
url = base+"/opac-search.pl?idx=&q="
suffix = "+&branch_group_limit="


def seekKohaSearch(bookcode):

    result = urlopen(url+bookcode+suffix).read()
    print(url+bookcode+suffix)
    # print(result)
    # <input type="hidden" name="bib" value="2969867">
    # >> m = re.search('(?<=-)\w+', 'spam-egg')
    # >>> m.group(0)
    # 'egg'
    m = re.search('(.*name="bib" value=")(\w+)', result)

    if (m is not None):
        tul = m.group(2)
    else:
        tul = "ERROR with Koha, with id: " + bookcode
    # print("!!!", tul)
    return tul


def seekKohaMarc(bookcode):
    url = base + "/opac-MARCdetail.pl?biblionumber="

    result = urlopen(url+bookcode).read()

    # grab from page the isbn part from MARC
    # print(result)
    # sys.exit(1)
    # aa = result.split('International Standard Book Number')[1]

    try:
        aa = result.split('ISBN-tunnus, International Standard Book Number')[1]
    except:
        aa = ""
        return ""

    bb = aa.split('040 ## - Luetteloiva')[0]

    # and finally the isbn
    m = re.search('<td>(\d+).*?</td>', bb)
    res = m.group(1)

    print("*** Koha id: {0} --> ISBN: {1}".format(bookcode, res))
    if (len(res) < 9):
        print("ERR: issue with getting proper id for {0} RAW:{1}".format(
            bookcode, bb))
        sys.exit(1)

    return res


def parseKohaEmail2(emailstr, codes="seuraavat niteet", library="lumme"):
    # print("email found: ", emailstr)
    bookids = []
    lineid = 0  # every evem line has ids.

    # tODO : how to find the end of book listing...
    if library == 'lumme':
        emailstr = emailstr.split("Lainasit seuraavat niteet:")[
            1].split("Kiitos")[0]
    if library == 'kaakkuri':
        emailstr = emailstr.split('Lainat')[1].split('Teoksia')[0]
    lineid = 1
    # sys.exit(1)
    #print("Starting listing books...", emailstr)
    for line in emailstr.split("\n")[1:]:
        if (len(line) < 4):
            pass

        bookname = line.split("/")[0].strip()
        print("{1} Kirja: <{0}>".format(bookname, lineid))

        # words = line.split(" ")
        if (lineid > 6 and len(bookname) == 0):
            lineid += 1
            continue  # hmmm...

        if lineid % 2 == 0:
            lineid += 1
            continue

        if library != 'lumme':
            match = re.search(r"[^0-9]+", bookname)
        else:
            match = bookname

        if match:
            #print("Haetaan finnast: {0} ({1}-kirjastosta).".format(bookname, library))
            stuff = seekFinnabyName(bookname, library)
            if (len(stuff) > 0):
                stuff = getFinnaRecord(stuff)  # returns isbn
            else:
                stuff = "NOTFOUND:"+bookname
            # print("Tulos: ", stuff)
            bookids.append(stuff)

        lineid += 1

    # print("Books found:", bookids)
    # sys.exit(1)

    return bookids


def parseKohaEmail(emailstr):
    print("email found: ", emailstr)
    kohaids = []
    lineid = 0  # every evem line has ids.

    emailstr = emailstr.split("Lainat")[1].split("Teoksia")[0]
    # print("Kasiteltava...", emailstr)
    lineid = 1
    # sys.exit(1)
    for line in emailstr.split("\n")[1:]:

        if (len(line) < 4):
            pass

        # print("Rivi!: {0}".format(line))

        bookname = line.split("/")[0]
        # print("{1} Kirja: {0}".format(bookname, lineid))

        # words = line.split(" ")

        if lineid % 2 == 0:
            lineid += 1
            continue

        match = re.search(r"[^0-9]+", bookname)

        if match:
            stuff = seekFinnabyName(bookname, 'kaakkuri')
            stuff = getFinnaRecord(stuff)  # returns isbn
            # print("Tulos: ", stuff)
            kohaids.append(stuff)

        lineid += 1

    # print("Books found:", kohaids)
    # sys.exit(1)

    return kohaids


def giveBookDetails(bookcode, isbn):
    url = base + "/opac-MARCdetail.pl?biblionumber="

    print(url)
    bookcode = seekKohaSearch(isbn)
    print(bookcode)

    result = urlopen(url+bookcode).read()

    #  #Need: at minimum: title, author, publisher, year published

    # TODO: Cleanup & regexify

    # grab from page the isbn part from MARC
    try:
        aa = result.split('International Standard Book Number')[1]
        bb = aa.split('040 ## - Luetteloiva')[0]
        # and finally the isbn
        m = re.search('<td>(\d+).*?</td>', bb)
        res = m.group(1)
    except:
        res = isbn

    # grab from page the isbn part from MARC
    try:
        aa = result.split('245 10 - Nimeke- ja vastuullisuusmerkintö')[1]
        bb = aa.split('Päänimeke')[1]
        m = re.search('<td>(.*?)\ \/</td>', bb)
        title = m.group(1)
        # print("Title:", title)
    except:
        title = "?"
        aa = result

    try:
        bb = aa.split("Vastuullisuusmerkinnöt jne.")[1]
        m = re.search('<td>(.*?)\.</td>', bb)
        author = m.group(1)
        # print("Author:", author)
    except:
        author = "author?"

    try:
        aa = result.split("Julkaisijan/kustantajan, jakajan jne. nimi")[1]
        m = re.search('<td>(.*)\,*</td>', aa)
        publisher = m.group(1)
    except IndexError:
        # print(">>> resu", result, "\n")
        publisher = ""
        print("Publisher:", publisher)

    try:
        aa = result.split("Julkaisu-, jakelu- jne. aika")[1]
        m = re.search('<td>(\d+)\.*\ *</td>', bb)
        pubyear = m.group(1)
    except IndexError:
        print("No year got :( ")
        pubyear = ""
    # print("Pubyear:", pubyear)

    return (title, author, isbn, publisher, pubyear)


# id   = seekKohaSearch("49120180709218")
# isbn = seekKohaMarc(id)

# isbn = "9789525132977"
# id = seekKohaSearch(isbn)
# print(id)

# aaa= giveBookdetails(id, isbn)
# bookdets = (aaa[0],aaa[1],aaa[2],"","",aaa[3],"",aaa[4])
# print ("Kirja:", bookdets)

# print("!",aaa[3])


# from tpcsvutils import writeToCSV

# Title, Author, ISBN, My Rating, Average Rating, Publisher, Binding, Year Published, Original Publication Year,
# writeToCSV('koe2.csv', bookdets)

# print("Thanks, come again :)")
