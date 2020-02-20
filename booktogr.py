#!/usr/bin/env python

import argparse
from imapexpr import getLastEmailBySubject
from kohatogr import parseKohaEmail, parseKohaEmail2, giveBookDetails
from tpcsvutils import writeToCSV
from finbooks import parseFEmail, seekBookbyISBN
import simplejson as json
import pprint
import sys
from betterreads import client
from goodreads_keys import grkey, grsecret, tok1, tok2, user, password
from rauth.service import OAuth1Service, OAuth1Session


def chkGoodReads(myisbn):

    gc = client.GoodreadsClient(grkey, grsecret)

    isbn = "978-055-38-0371-6"
    # url = "https://www.goodreads.com/search[isbn]="+isbn

    try:
        book = gc.book(isbn=myisbn)
    except:
        print("Book with isbn {0} not found(?)\n".format(myisbn))
        return (0, 0)

    print("\n", book.authors[0].name)
    print(book.title, book.gid)
    # , "by ", codecs.decode(str(book.authors[0].name))
    # , "\n", book.description , "\n"

    return (1, book)


def grExistingSession(token1, token2):

    new_session = OAuth1Session(
        consumer_key=grkey,
        consumer_secret=grsecret,
        access_token=token1,
        access_token_secret=token2,
    )

    return new_session


def addtoReading(myisbn):
    gc = client.GoodreadsClient(grkey, grsecret)
    gc.authenticate(tok1, tok2)

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
    print("Book found: gid:" + str(gid) + " isbn:", str(myisbn))

    # if there is reason to believe that old session is not working
    ##session = graskaccess()

    #(tok1, tok2) = gettokens()
    session = grExistingSession(tok1, tok2)

    res = session.post('https://www.goodreads.com/shelf/add_to_shelf.xml', {
        'name': 'currently-reading',
        'book_id': gid
    })

    #print("result:", res)
    return res


if __name__ == "__main__":

    # todo : Add info about need to give either -e or -a
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
    subjectstr = "Lainat"

    if args.library2:
        mylibrary = 'kaakkuri'
        codeword = 'Lainat'
        subjectstr = "Lainauskuitti"

    if (args.email):
        mylibrary = "lumme"
        codeword = "niteet:"  # helps to detect where teh book info starts

    recentLoans = getLastEmailBySubject(user, password, subjectstr)

    #print(">>>", recentLoans)
    books = parseKohaEmail2(recentLoans, codeword, mylibrary)

    print("Books got: ", books)
    # sys.exit(1)

    books.extend(books2)

    for book in books:
        # if len(book) > 0:
        if book is not None:
            ok = addtoReading(book)
            print("OK? {0}".format(ok))
        # TODO: if noticing that a book was nonexistent, add to a csv for creating a new item
        # if not "[201]" in ok:
        #    addtoMissing(book)  # TODO , not working for all books yet...

    print("All done, bye!")
