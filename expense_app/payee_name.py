import imaplib
import re
from sys import getsizeof
import socket


def is_connected():
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        pass
    return False

if (is_connected()):
    print("connected to internet")
    # global regex pattern for the getting payee name from mail
    regex = r"(?=ATD:|\?<=PCA:)?([a-zA-Z]+)?(\.+)?([a-zA-Z]+)?(\/)?(?:\s{0,20})(?:[a-zA-Z]+)?(\/)?[a-zA-Z]?(\.+)?(?:\s{0,20})?(\.+)?(?:[a-zA-Z]+)?(\.+)?(?:\s{0,20})?(\.+)?(?:[a-zA-Z]+)?(\.+)?(?:\s{0,20})?(\.+)?(?:[a-zA-Z]+)?(\.+)?(?:\s{0,20})?(\.+)?(?:\s{0,20})(?=Available)"

    mail = imaplib.IMAP4_SSL('imap.gmail.com')

    login = mail.login('budget.expenseapp@gmail.com', 'dscw1800')

    mail.select("inbox")
    extraction = list()
    result, data = mail.search(None, '(UNSEEN)', '(FROM "alerts@yesbank.in" SUBJECT "Account Debit Alert")')
    try:
        for num in data[0].split():
            typ, data = mail.fetch(num, '(RFC822)')
            raw_email = data[0][1]
            try:
                match = re.search(regex, raw_email)
            except:
                raw_email = raw_email.decode('utf-8')
                match = re.search(regex, raw_email)
            if (match!=None):
                try:
                    finalresult = ' '.join(match.group().split())
                except:
                    finalresult = ' '.join(match.split())
                extraction.append(finalresult)
    except Exception as e:
        print("Exception", e)

    print(extraction)
else:
    print("No Internet connection")