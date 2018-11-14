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
    # global regex pattern for the getting payee name from mail
    regex = r"(?=ATD:|\?<=PCA:)?([a-zA-Z]+)?(\.+)?([a-zA-Z]+)?(\/)?(?:\s{0,20})(?:[a-zA-Z]+)?(\/)?[a-zA-Z]?(\.+)?(?:\s{0,20})?(\.+)?(?:[a-zA-Z]+)?(\.+)?(?:\s{0,20})?(\.+)?(?:[a-zA-Z]+)?(\.+)?(?:\s{0,20})?(\.+)?(?:[a-zA-Z]+)?(\.+)?(?:\s{0,20})?(\.+)?(?:\s{0,20})(?=Available)"
    regexAmount = r"[0-9]+(\,)?[0-9]+?(\.)[0-9]+?(\s{0,2})(?=Debited)"
    mail = imaplib.IMAP4_SSL('imap.gmail.com')

    login = mail.login('budget.expenseapp@gmail.com', 'dscw1800')

    mail.select("inbox")
    extraction = list()
    resutlDict = {}
    result, data = mail.search(None, '(UNSEEN)', '(FROM "alerts@yesbank.in" SUBJECT "Account Debit Alert")')
    try:
        for num in data[0].split():
            typ, data = mail.fetch(num, '(RFC822)')
            raw_email = data[0][1]
            resutlDict[num] = {}
            try:
                # match = re.search(regexAmount, raw_email)
                matchAmount = re.search(regexAmount, raw_email)
            except:
                raw_email = raw_email.decode('utf-8')
                # match = re.search(regex, raw_email)
                matchAmount = re.search(regexAmount, raw_email)
            if (matchAmount!=None):
                try:
                    finalresult = ' '.join(matchAmount.group().split())
                    # resutlDict.update("payee"=match)
                    resutlDict[num]['amount'] = matchAmount
                except:
                    finalresult = ' '.join(matchAmount.split())
                    # resutlDict.update("payee"=match)
                    resutlDict[num]['amount'] = matchAmount
                print(resutlDict[num])
                extraction.append(finalresult)
    except Exception as e:
        print("Exception", e)

    print("All results", extraction)
    print("Dictionary result", resutlDict)
else:
    print("No Internet connection")