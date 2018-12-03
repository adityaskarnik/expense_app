import imaplib
import re
from sys import getsizeof
import socket
import sqlite3
import os
from datetime import datetime
cwd = os.getcwd()
database = cwd+"/db.sqlite3"
print(database)

def is_connected():
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        pass
    return False

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        print("Exception", e)
 
    return None

def create_project(conn, expense):
    sql = ''' INSERT INTO expenses(expense_date,amount,category,sub_category,payment_method,description,
                ref_no,payee,status,receipt_picture,account,tag,tax,mileage)
    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''
    cur = conn.cursor()
    cur.execute(sql, expense)
    return cur.lastrowid

if (is_connected()):
    # global regex pattern for the getting payee name from mail
    regexPayeeName = r"(?=ATD:|\?<=PCA:)?([a-zA-Z]+)?(\.+)?([a-zA-Z]+)?(\/)?(?:\s{0,20})(?:[a-zA-Z]+)?(\/)?[a-zA-Z]?(\.+)?(?:\s{0,20})?(\.+)?(?:[a-zA-Z]+)?(\.+)?(?:\s{0,20})?(\.+)?(?:[a-zA-Z]+)?(\.+)?(?:\s{0,20})?(\.+)?(?:[a-zA-Z]+)?(\.+)?(?:\s{0,20})?(\.+)?(?:\s{0,20})(?=Available)"
    regexAmount = r"[0-9]+(\,)?[0-9]+?(\.)[0-9]+?(\s{0,2})(?=Debited)"
    regexDate = r"[0-9]{0,2}-[A-Z]{0,3}-[0-9]{0,4}\s[0-9]+?:[0-9]+?:[0-9]+"
    mail = imaplib.IMAP4_SSL('imap.gmail.com')

    login = mail.login('budget.expenseapp@gmail.com', 'dscw1800')

    mail.select("inbox")
    resutlDict = {}
    result, data = mail.search(None, '(UNSEEN)', '(FROM "alerts@yesbank.in" SUBJECT "Account Debit Alert")')
    try:
        for num in data[0].split():
            typ, data = mail.fetch(num, '(RFC822)')
            raw_email = data[0][1]
            resutlDict[num] = {}
            try:
                matchPayeeName = re.search(regexPayeeName, raw_email)
                matchAmount = re.search(regexAmount, raw_email)
            except:
                raw_email = raw_email.decode('utf-8')
                matchPayeeName = re.search(regexPayeeName, raw_email)
                matchAmount = re.search(regexAmount, raw_email)
                matchDate = re.search(regexDate, raw_email)

                # TODO add condition to skip ATD payee type

            if (matchAmount is not None and matchDate is not None):
                try:
                    date = datetime.strptime(matchDate.group().split()[0],'%d-%b-%Y').strftime('%Y/%m/%d')
                    resutlDict[num]['payee'] = matchPayeeName.group()
                    resutlDict[num]['amount'] = matchAmount.group()
                    resutlDict[num]['date'] = date

                except Exception as e:
                    print ("Finalresult Exception", e)
                    date = datetime.strptime(matchDate.group().split()[0],'%d-%b-%Y').strftime('%Y/%m/%d')
                    resutlDict[num]['payee'] = matchPayeeName.group()
                    resutlDict[num]['amount'] = matchAmount.group()
                    resutlDict[num]['date'] = date
                conn = create_connection(database)
                with conn:
                    print("connection created")
                    # Date, Amount, Category, Sub Category, Payment Method, Description, 
                    # Ref/Check No, Payee / Payer, Status, Receipt Picture, Account, Tag, Tax, Mileage
                    # create a new project
                    expense = (date, matchAmount.group(), 'Personal', 'Unknown', 'Debit Card', '', '', matchPayeeName.group(),
                    'Cleared', '', 'Personal Expense', '', '', '')
                    create_project(conn, expense)
            else: 
                print("Regex search failed")

    except Exception as e:
        print("Exception", e)

    print("Dictionary result", resutlDict)
else:
    print("No Internet connection")