#!/usr/bin/env python

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

from kohatogr import parseKohaEmail, giveBookDetails
from tpcsvutils import writeToCSV


#utilizes gr example at:
#https://www.goodreads.com/api/oauth_example#python

# for the email part
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Book to Gr'


from goodreads import client
import codecs
import pprint
import simplejson as json
from collections import OrderedDict
from goodreads_keys import grkey,grsecret

#grkey=""
#grsecret=""


def percent_encoding(string):
    #from  https://stackoverflow.com/a/48117815/364931
    result = ''
    accepted = [c for c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~'.encode('utf-8')]
    for char in string.encode('utf-8'):
        result += chr(char) if char in accepted else '%{}'.format(hex(char)[2:]).upper()
    return result


def chkGoodReads (myisbn):

  gc = client.GoodreadsClient(grkey, grsecret)

  isbn="978-055-38-0371-6"
  #url = "https://www.goodreads.com/search[isbn]="+isbn

  try:
  	book=gc.book(isbn=myisbn)
  except:
    print "Book with isbn {0} not found(?)\n".format(myisbn)
    return (0,0)


  print "\n", book.authors[0].name
  print book.title , book.gid
  #, "by ", codecs.decode(str(book.authors[0].name))
  #, "\n", book.description , "\n"


  return (1,book)



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
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def ListMessagesMatchingQuery(service, user_id, query=''):
    """List all Messages of the user's mailbox matching the query.
    """
    try:
        response = service.users().messages().list(userId=user_id,q=query).execute()
        messages=[]
        if 'messages' in response:
            messages.extend(response['messages'])
        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id, q=query, pageToken=page_token).execute()
            messages.extend(response['messages'])
        return messages
    except errors.HttpError, error:
        print('An error occurred: %s' % error)


def GetMimeMessage(service, user_id, msg_id):
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
                                             format='raw').execute()

    msg = message['snippet'].encode('utf-8')
    ##print('Message snippet: %s' % msg )

    msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))    

    return msg_str

  except errors.HttpError, error:
    print('An error occurred: %s' % error)


def chkLoanEmail():

  credentials = get_credentials()
  http = credentials.authorize(httplib2.Http())
  
  service = discovery.build('gmail', 'v1', http=http)
  labels = []

  labels =  ListMessagesMatchingQuery(service,'me','Lainat')

  #Pick up just newest email of specific topic
  label = labels[0]
  print("Latest id:", label['id'])
  bodystr = GetMimeMessage(service,'me',label['id'])
  bodystr = bodystr.split('Lainasit seuraavat niteet:')[1]
  bodystr = bodystr.replace('\n</p>','')

  import quopri
  bodystr = quopri.decodestring(bodystr).decode('utf-8')  #fixes  etc style from raw email

  #print(bodystr)
  return bodystr #list of loaned books from email.


def storetokens(tok1,tok2):

  home_dir = os.path.expanduser('~')
  credential_dir = os.path.join(home_dir, '.credentials')
  credfile = credential_dir+'/'+"goodreads.tmp"

  import shelve
  creds = shelve.open(credfile)
  creds['TOKEN']=tok1
  creds['TOKENS']=tok2

  creds.close()


def gettokens():
  home_dir = os.path.expanduser('~')
  credential_dir = os.path.join(home_dir, '.credentials')
  credfile = credential_dir+'/'+"goodreads.tmp"

  import shelve
  creds = shelve.open(credfile)

  return [creds['TOKEN'],creds['TOKENS']]


def graskaccess():

  #https://www.goodreads.com/api/oauth_example#python
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
  request_token, request_token_secret = goodreads.get_request_token(header_auth=True)
  authorize_url = goodreads.get_authorize_url(request_token)
  print 'Visit this URL in your browser: ' + authorize_url
  accepted = 'n'
  while accepted.lower() == 'n':
      # you need to access the authorize_link via a browser,
      # and proceed to manually authorize the consumer
      accepted = raw_input('Have you authorized me? (y/n) ')

  session = goodreads.get_auth_session(request_token, request_token_secret)
  #print "TOKEN:", session.access_token
  #print "SECR:", session.access_token_secret

  storetokens(session.access_token,session.access_token_secret)

  return session


def grExistingSession (token1,token2):

  new_session = OAuth1Session(
    consumer_key = grkey,
    consumer_secret = grsecret,
    access_token = token1,
    access_token_secret = token2,
  )

  return new_session

def addtoReading(myisbn):

    gc = client.GoodreadsClient(grkey, grsecret)
    gc.authenticate(grkey,grsecret)

    pp = pprint.PrettyPrinter(indent=4)

    (res,mibook) = chkGoodReads(myisbn)

    if (res==0):
        print("Sorry, book with isbn: {0} not found in GR".format(myisbn) )
        return 0

    #TODO 2 diff ways to access gr, remove 1   
    #grbookid = session.get('https://www.goodreads.com/book/isbn_to_id',
    #  {'isbn' : myisbn})
    #print grbookid

    gid = mibook.gid
    print("Book found: gid:"+gid + " isbn:",myisbn)

    #if there is reason to believe that old session is not working
    #session = graskaccess()
    (tok1,tok2)=gettokens()
    session = grExistingSession(tok1,tok2)
    

    res = session.post('https://www.goodreads.com/shelf/add_to_shelf.xml', {
      'name':'currently-reading',
      'book_id': gid
    })

    print("result:",res)


def addtoMissing(isbn):
    
    print("Data got: ", isbn)
    #9789525132977
    book = giveBookDetails(id, isbn)
    bookdets = (book[0],book[1],book[2],"","",book[3],"",book[4])
    
    from tpcsvutils import writeToCSV
    #Title, Author, ISBN, My Rating, Average Rating, Publisher, Binding, Year Published, Original Publication Year,
    writeToCSV('koe2.csv', bookdets)




if __name__ == "__main__":

    #todo : Add info about need to give either -e or -a
    import argparse
    parser = argparse.ArgumentParser(description='From email to goodreads')
    parser.add_argument("-i", "--isbn", dest="isbn",
                  help="add individual isbn to reading list")

    parser.add_argument("-a", "--add", dest="add", 
                  help="add a missing book to the csv list")

    parser.add_argument("-e", "--email", dest="email", default=False,action="store_true",
                  help="check books from email and add them to reading list")


    args = parser.parse_args()


    if (args.email):
      print("Checking email for recent loans...")
      recentLoans = chkLoanEmail()
      print(recentLoans)
      books = parseKohaEmail(recentLoans)

      for book in books:
        ok = addtoReading(book)
        #TODO: if noticing that a book was nonexistent, add to a csv for creating a new item
        if not ok:
            addtoMissing(book)


    if (args.isbn):
        addtoReading(args.isbn)

    if (args.add):
        addtoMissing(args.add)
        

