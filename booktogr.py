#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
from goodreads_keys import grkey, grsecret
from collections import OrderedDict
import simplejson as json
import pprint
import codecs
from goodreads import client as grclient
import base64
import email
import json
import os
import re
import urllib
import urllib2
import sys

import BeautifulSoup
import httplib2
import requests
import HTMLParser

from apiclient import discovery, errors
from oauth2client import client, tools
from oauth2client.file import Storage
from rauth.service import OAuth1Service, OAuth1Session

from kohatogr import parseKohaEmail, parseKohaEmail2, giveBookDetails
from tpcsvutils import writeToCSV
from finbooks import parseFEmail, seekBookbyISBN


# utilizes gr example at:
# https://www.goodreads.com/api/oauth_example#python

# for the email part
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Book to Gr'


# grkey=""
# grsecret=""


def percent_encoding(string):
    # from  https://stackoverflow.com/a/48117815/364931
    result = ''
    accepted = [
        c for c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~'.encode('utf-8')]
    for char in string.encode('utf-8'):
        result += chr(char) if char in accepted else '%{}'.format(hex(char)
                                                                  [2:]).upper()
    return result


def chkGoodReads(myisbn):

    gc = grclient.GoodreadsClient(grkey, grsecret)

    isbn = "978-055-38-0371-6"
    # url = "https://www.goodreads.com/search[isbn]="+isbn

    try:
        book = gc.book(isbn=myisbn)
    except:
        print "Book with isbn {0} not found(?)\n".format(myisbn)
        return (0, 0)

    print "\n", book.authors[0].name
    print book.title, book.gid
    # , "by ", codecs.decode(str(book.authors[0].name))
    # , "\n", book.description , "\n"

    return (1, book)


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def ListMessagesMatchingQuery(service, user_id, query=''):
    """List all Messages of the user's mailbox matching the query.
    """
    print("LMMQ. ", query)
    try:
        response = service.users().messages().list(userId=user_id, q=query).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])
        print("Messages amount now: ", len(messages))
        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(
                userId=user_id, q=query, pageToken=page_token).execute()
            messages.extend(response['messages'])
        return messages
    except errors.HttpError, error:
        print('An error occurred: %s' % error)


def GetMimeMessage(service, user_id, msg_id, optcont="Lainasit seuraavat niteet:"):
    """Get a Message and use it to create a MIME Message.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      msg_id: The ID of the Message required.

    Returns:
      A MIME Message, consisting of data from Message.
    """
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id,
                                                 format='full').execute()

        msg = message['snippet'].encode('utf-8')
        print('Message snippet: %s' % msg)

        # print(";".join(message.keys()))
        print(";".join(message['payload'].keys()))

        # todo, in some cases there is no data...(?)
        txts = message['payload']['body']['data'].encode('ASCII')

        msg_str = base64.urlsafe_b64decode(txts)
        #print("!!!", msg_str)

        # print("XXX", base64.urlsafe_b64decode(message['raw'].encode('ASCII')))
        # sys.exit(1)
        #print("Videsti:", message)
        # msg_str = base64.urlsafe_b64decode(message['payload'].encode('ASCII'))
        # ops = ""
        ##print("Viesti: {0} \n********\n".format(msg_str))
        # sys.exit(1)
        # try:
        #    ops = msg_str.split(
        #        "X-MS-Exchange-Transport-CrossTenantHeadersStamped")[1].split("\r\n\r\n")[1]
        # 3except IndexError:
        # ops = msg_str.split(optcont)[1].split("Kiitos ")[0]
        msg_str = msg_str.split(optcont)[0]  # hmm

        # if len(msg_str)==0:  #hmmm.
        #    msg_str = msg_str.split("Kiitos ")[1]

        # import quopri
        # ops = quopri.decodestring(ops).decode(
        #    'utf-8')  # fixes  etc style from raw email

        return msg_str

    except errors.HttpError, error:
        print('An error occurred: %s' % error)


def chkLoanEmail(subjectstr="Lainat", codestr="'Lainasit seuraavat niteet:'"):

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())

    print("Subject: {0} --Code: {1}".format(subjectstr, codestr))
    service = discovery.build('gmail', 'v1', http=http)
    labels = []

    labels = ListMessagesMatchingQuery(service, 'me', subjectstr)

    # Pick up just newest email of specific topic
    # newest one is the top one  1: if the returned email comes later.
    label = labels[0]
    #print("Latest id:", label['id'])
    bodystr = GetMimeMessage(service, 'me', label['id'], codestr)
    # print("Sisältö: {0}".format(bodystr))  # .encode('utf-8')

    return bodystr  # list of loaned books from email.


def storetokens(tok1, tok2):

    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    credfile = credential_dir+'/'+"goodreads.tmp"

    import shelve
    creds = shelve.open(credfile)
    creds['TOKEN'] = tok1
    creds['TOKENS'] = tok2

    creds.close()


def gettokens():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    credfile = credential_dir+'/'+"goodreads.tmp"

    import shelve
    creds = shelve.open(credfile)

    return [creds['TOKEN'], creds['TOKENS']]


def graskaccess():

    # https://www.goodreads.com/api/oauth_example#python
    goodreads = OAuth1Service(
        consumer_key=grkey,
        consumer_secret=grsecret,
        name='goodreads',
        request_token_url='https://www.goodreads.com/oauth/request_token',
        authorize_url='https://www.goodreads.com/oauth/authorize',
        access_token_url='https://www.goodreads.com/oauth/access_token',
        base_url='https://www.goodreads.com/'
    )

# head_auth=True is important here; this doesn't work with oauth2 for some reason
    request_token, request_token_secret = goodreads.get_request_token(
        header_auth=True)
    authorize_url = goodreads.get_authorize_url(request_token)
    print 'Visit this URL in your browser: ' + authorize_url
    accepted = 'n'
    while accepted.lower() == 'n':
        # you need to access the authorize_link via a browser,
        # and proceed to manually authorize the consumer
        accepted = raw_input('Have you authorized me? (y/n) ')

    session = goodreads.get_auth_session(request_token, request_token_secret)
    # print "TOKEN:", session.access_token
    # print "SECR:", session.access_token_secret

    storetokens(session.access_token, session.access_token_secret)

    return session


def grExistingSession(token1, token2):

    new_session = OAuth1Session(
        consumer_key=grkey,
        consumer_secret=grsecret,
        access_token=token1,
        access_token_secret=token2,
    )

    return new_session


def addtoReading(myisbn):

    gc = grclient.GoodreadsClient(grkey, grsecret)
    gc.authenticate(grkey, grsecret)

    pp = pprint.PrettyPrinter(indent=4)

    (res, mibook) = chkGoodReads(myisbn)

    if (res == 0):
        print("Sorry, book with isbn: {0} not found in GR".format(myisbn))
        return 0

    # TODO 2 diff ways to access gr, remove 1
    # grbookid = session.get('https://www.goodreads.com/book/isbn_to_id',
    #  {'isbn' : myisbn})
    # print grbookid

    gid = mibook.gid
    #print("Book found: gid:"+gid + " isbn:", myisbn)

    # if there is reason to believe that old session is not working
    # session = graskaccess()

    (tok1, tok2) = gettokens()
    session = grExistingSession(tok1, tok2)

    res = session.post('https://www.goodreads.com/shelf/add_to_shelf.xml', {
        'name': 'currently-reading',
        'book_id': gid
    })

    #print("result:", res)
    return res


def addtoMissing(isbn, filename="koe3.csv"):

    print("Data got: ", isbn)
    # 9789525132977  9789510363959
    # book = giveBookDetails(id, isbn)
    book = seekBookbyISBN(isbn)
    bookdets = (book[0], book[1], book[2], "", "", book[3], "", book[4])

    from tpcsvutils import writeToCSV
    # Title, Author, ISBN, My Rating, Average Rating, Publisher, Binding, Year Published, Original Publication Year,
    writeToCSV(filename, bookdets)
    print("file to import to GR created {0}".format(filename))


if __name__ == "__main__":

    # todo : Add info about need to give either -e or -a
    import argparse
    parser = argparse.ArgumentParser(description='From email to goodreads')
    parser.add_argument("-i", "--isbn", dest="isbn",
                        help="add individual isbn to reading list")

    parser.add_argument("-a", "--add", dest="add",
                        help="add a missing book to the csv list")

    parser.add_argument("-e", "--email", dest="email", default=False, action="store_true",
                        help="check books from email and add them to reading list")

    parser.add_argument("-x",  dest="library2", default=False, action="store_true",
                        help="check books from email of library2 and add them to reading list")

    args = parser.parse_args()
    books = []
    books2 = []

    codeword = None
    mylibrary = 'lumme'

    if args.library2:
        mylibrary = 'kaakkuri'
        codeword = 'Lainat'

    if (args.email):
        print("Checking email for recent loans...")
        recentLoans = chkLoanEmail("Lainat")

        books = parseKohaEmail2(recentLoans, codeword, mylibrary)

    # books = books.append(books2)
    print("Kirjaset: ", books2)

    books.extend(books2)

    for book in books:
        # if len(book) > 0:
        if book is not None:
            ok = addtoReading(book)
            print("OK? {0}".format(ok))
        # TODO: if noticing that a book was nonexistent, add to a csv for creating a new item
        # if not "[201]" in ok:
        #    addtoMissing(book)  # TODO , not working for all books yet...

    if (args.isbn):
        addtoReading(args.isbn)

    if (args.add):
        addtoMissing(args.add)
