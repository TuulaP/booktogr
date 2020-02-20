#!/usr/bin/env python

import sys
import imaplib
import email
mail = imaplib.IMAP4_SSL('imap.gmail.com')
# imaplib module implements connection based on IMAPv4 protocol


def getLastEmailBySubject(user, password, subjectstr):

    print("Checking email...")
    mail.login(user, password)
    mail.select('inbox')  # Connected to inbox.

    # TODO 1st is charset

    # these didn't work
    #result, data = mail.search(None, "FROM", "kampuskirjasto.mikkeli")
    #result, data = mail.search(None, "X-GM-RAW", "subject: Lainauskuitti")
    #result, data = mail.search(None, '(SUBJECT "Lainauskuitti")')

    searchstr = '(SUBJECT "{0}")'.format(subjectstr)
    #print("Searching for ({0})".format(searchstr))

    result, data = mail.uid('search', None, searchstr)

    i = len(data[0].split())  # data[0] is a space separate string

    bodystr = ""

    for x in range(i-1, i-2, -1):
        #x = i-1

        #print("X is {0}".format(x))
        # need just the latest

        latest_email_uid = data[0].split()[x]  # unique ids wrt label selected
        result, email_data = mail.uid('fetch', latest_email_uid, '(RFC822)')
        # fetch the email body (RFC822) for the given ID

        if email_data[0] is None:
            pass

        raw_email = email_data[0][1]

        try:
            raw_email_string = raw_email.decode('utf-8')
        except:
            raw_email_string = raw_email.decode('iso-8859-1')

        # converts byte literal to string removing
        email_message = email.message_from_string(raw_email_string)
        # this will loop through all the available multiparts in mail

        for part in email_message.walk():
            if part.get_content_type() == "text/plain":  # ignore attachments/html

                body = part.get_payload(decode=True)
                try:
                    print("1: {0} ".format(
                        latest_email_uid), body.decode('utf-8'))
                    bodystr = body.decode('utf-8')
                except:
                    print("2: ", body.decode('iso-8859-1'))
                    bodystr = body.decode('iso-8859-1')
            else:
                continue

    return bodystr


#content = getLastEmailBySubject(user, password, "Lainauskuitti")
#print("SSS", content)
