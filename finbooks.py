#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Book data from finna by isbn, name

import urllib.request
#from urllib import urlopen
import pprint
import simplejson as json
# from booktogr import chkGoodReads
import sys

#from kitchen.text.converters import getwriter

url = "https://api.finna.fi/v1/search?lookfor="
CSVSEP = ";"
QUOTE = '"'
full = "&field[]=fullRecord"
recordurl = "https://api.finna.fi/v1/record?id="
suffix = "&field[]=id"
FLTR = "&filter[]=~"
booktype = '&filter[]=~format_ext_str_mv="1/Book/Book/"'


builcodes = {
    'helmet': 'building:"0/Helmet/"',
    'kaakkuri': 'building:"0/XAMK/"',
    'lumme': 'building:"0/Lumme/"',
}

marcfields = {
    'title': '245', 'author': '100',
    'publisher': '264', 'pubyear': '264',
    'isbn': '020'
}


def parseFEmail(emailstr):
    print("F.email found: ", emailstr)
    bookids = []
    lineid = 0  # every evem line has ids.
    alku = 1
    alkub = 0
    osuus = emailstr.split("Lainat")[1]
    # print("xxxx - osuus", osuus)

    for line in osuus.split("\r\n")[1:]:  # emailstr.split("\r\n"):
        # if "primal" in line:
        print("xxx {0} : {1}".format(lineid, line))
        words = line.split(" ")

        if lineid == 1:
            alku = 1

        if "Teoksia yhteens" in line:
            break

        if alku:
            # if lineid % 2 == 0:  # viivakoodi -> ei voi hakea ; name
            print("Processingx: ", words[0])
            # pass
        # else:
            bookid = line.split("/")[0] + "*"
            #bookid = line + "*"
            #bookid = bookid.split(" ")[0]
            # if (len(bookid) > 3):
            #    # pass
            #    # print("sss")
            #    print("bookid", bookid)###

            #    isbn = getFinnaRecord(seekFinnabyName(bookid))
            #    bookids.append(isbn)
            #    isbn = ""
            #    bookid = ""
        lineid += 1

    print("Books found:", bookids)
    return bookids


def getMarcValue(record, name='title'):

    # record.get_fields('245')
    value = []
    fi = marcfields[name]
    pref = ""

    if (name == 'title'):
        pref = ' '

    for f in record.get_fields(fi):
        #print("kentta:", f['a'])
        value.append(f['a'].replace("-", ""))

        if 'b' in f:
            try:
                value.append(pref + f['b'].replace("/", ""))
            except TypeError:
                pass
        if 'c' in f:
            if name == 'pubyear':
                value = f['c']

    if (name == 'publisher'):
        value = value[-1]  # drop a

    if (name == 'author'):
        names = value[0].split(", ")
        value = [names[-1].replace(",", ""), " " + names[0]]

    # print("".join(value))
    return "".join(value)


def seekBookbyISBN(isbn, library="helmet"):

    library = builcodes[library]

    ##print("XXX", url+isbn+full+FLTR+library)

    result = urllib.request.urlopen(url+isbn+full+FLTR+library).read()
    result = json.loads(result)
    result = result.get('records')

    # print "data searched:" + url + isbn + "\n"
    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(result)

    resultSet = result[0]

    xmlmarc = result[0]['fullRecord']

    # todo unnecessary bit...

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

    title = getMarcValue(record, 'title')
    author = getMarcValue(record, 'author')
    publisher = getMarcValue(record, 'publisher').replace(",", "")
    pubyear = getMarcValue(record, 'pubyear').replace(".", "")

    #print("Valittu ISBN: {0}, title {1}".format(isbn, title.encode('utf-8')))

    return (title, author, isbn, publisher, pubyear)


def seekFinnabyName(bookname, library="helmet"):

    library = builcodes[library]
    bookname = urllib.parse.quote(bookname)  # TODO - this to elsewhere
    # bookname.decode('utf-8')

    #print("URL: ", url+bookname+FLTR+library+suffix)

    result = urllib.request.urlopen(url+bookname+FLTR+library+suffix).read()
    result = json.loads(result)
    result = result.get('records')

    # print "data searched:" + url + isbn + "\n"
    #pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(result)
    if result:
        resultSet = result[0]
        print(result[0]['id'])
        return result[0]['id']
    else:
        return ""


def getFinnaRecord(bookid):

    #print("GetFinnaRecord: ", recordurl+bookid+full)

    result = urllib.request.urlopen(recordurl+bookid+full).read()
    result = json.loads(result)
    result = result.get('records')

    # print ">>", bookid, "\n"

    xmlmarc = result[0]['fullRecord']

    #print(">>", xmlmarc)
    import sys

    # pp = pprint.PrettyPrinter(indent=4)
    with open("kirja.xml", "w") as text_file:
        text_file.write(xmlmarc)  # str(xmlmarc.encode("UTF-8")))
    #
    from pymarc import parse_xml_to_array, record_to_xml

    # NB , 020 (R)
    hackish = xmlmarc.split('tag="020"')[1].split(
        "</subfield>")[0].split('a">')[1]
    #print(">>", hackish)
    isbn = hackish
    if " " in isbn:
        isbn = isbn.split(" ")[0]  # some cases have (.sid) or (.nid) in isbn

    nimeke = xmlmarc.split('tag="245"')[1].split(
        "</subfield>")[0].split('a">')[1]
    nimeke = nimeke[:-2]
    #print(">!>", nimeke)

    #xmlmarc = xmlmarc.split("<record>")[1]
    #xmlmarc = "<record>"+xmlmarc
    #xx = record_to_xml(xmlmarc)
    # print(xx)

    # reader = parse_xml_to_array(xmlmarc)  # (xmlmarc)  # "kirja.xml")

    #         isbn = record['020']['a']

    details = {}

    # import re
    # isbn = ""
    # isbns = []

    # for record in reader:

    #     for f in record.get_fields('020'):
    #         #print("kentta:", f['a'])
    #         if f['a'] is None:
    #             return "NOSIBN?"
    #         isbns.append(f['a'].replace("-", ""))

    #     try:
    #         isbn = record['020']['a']
    #     except TypeError:
    #         pass

    # if (len(isbns) > 1):
    #     if (len(isbns[0]) > len(isbns[1])):
    #         isbn = isbns[0]

    #     if (len(isbns[1]) > len(isbns[0])):
    #         isbn = isbns[1]

    # if record['245'] is not None:
    #     nimeke = record['245']['a']
    #     if record['245']['b'] is not None:
    #         nimeke = nimeke + " " + record['245']['b']

    print("Valittu teos: {0}, {1}".format(
        isbn.strip(), nimeke.encode('utf-8')))

    return isbn.replace("-", "")


# ysid = seekFinnabyName(
#    "Rocket surgery made easy : the do-it-yourself guide to findi*")

# "Primal leadership : unleashing the power of emotional intell*")

#isbn = getFinnaRecord(ysid)
#print("ISBN: ", isbn)
# seekBookbyISBN("978-952-215-680-8")
