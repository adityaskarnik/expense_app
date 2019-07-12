import imaplib
import re
from sys import getsizeof
import socket
import sqlite3
import os
from datetime import datetime
from celery import Celery
from celery.schedules import crontab

app = Celery('mail_checker')

cwd = os.getcwd()
database = cwd+"/db.sqlite3"
definedPayees = {'Food': {'Restaurant' : ['Zomato', 'CureFit', 'Diverse Retails']}, 
                'Travel': {'Taxi' : ['Uber','Zaak']}, 
                'Utilities' : {'Telephone' : ['Vodafone'], 
                'Internet' : ['ACTCORP', 'JIOMONEY']},
                'Personal' : {'Clothing' : ['Myntra'], 'Others': ['DUNZO']}, 
                'Home Office': {'Other': ['LINKEDIN', 'RESUME', 'Zety', 'AMAZON INTERNET']}, 
                'Entertainment' : {'Other' : ['ITUNES', 'NETFLIX']},
                'Household' : {'Rent' : ['rent']},
                'Savings' : {'RD' : ['MonthlyRD'], 'PPF' : ['PPF']}}

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(hour='*/6'),mail_checker.s())
    # sender.add_periodic_task(crontab(minute='*'),mail_checker.s())

def is_connected():
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        socket.create_connection(("www.google.com", 80))
        print('Internet check')
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
    sql = ''' INSERT INTO expenses(date,amount,category,sub_category,payment_method,description,
                ref_checkno,payee_payer,status,receipt_picture,account,tag,tax,mileage)
    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''
    cur = conn.cursor()
    cur.execute(sql, expense)
    return cur.lastrowid

@app.task
def mail_checker():
    if (is_connected()):
        print('Process started')
        # global regex pattern for the getting payee name from mail
        regexPayeeName = r"((?<=PCA:[0-9]{10}:).*(?=Available))|((?<=(to|To)):?[0-9a-zA-Z.\s@\/]+((?=UTRNO)|(?=Available)))"
        regexAmount = r"((?<=INR\s).*(?=\sDebited))|(?<=INR\s).*(?=\shas)"
        regexDate = r"[0-9]{0,2}-[A-Z]{0,3}-[0-9]{0,4}\s[0-9]+?:[0-9]+?:[0-9]+"
        mail = imaplib.IMAP4_SSL('imap.gmail.com')

        login = mail.login('budget.expenseapp@gmail.com', os.environ["BUDGET_PASSWORD"])

        mail.select("inbox")
        resutlDict = {}
        result, data = mail.search(None, '(UNSEEN)', '(FROM "alerts@yesbank.in" OR FROM "aditya.s.karnik@gmail.com" HEADER Subject "Debit Alert")')
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
                        resutlDict[num]['payee'] = " ".join(matchPayeeName.group().split())
                        resutlDict[num]['amount'] = matchAmount.group()
                        resutlDict[num]['date'] = date

                    except Exception as e:
                        print ("Finalresult Exception", e)
                        try:
                            date = datetime.strptime(matchDate.group().split()[0],'%d-%b-%Y').strftime('%Y/%m/%d')
                        except:
                            date = datetime.strptime(matchDate.group().split()[0],'%d-%b-%y').strftime('%Y/%m/%d')
                        resutlDict[num]['payee'] = " ".join(matchPayeeName.group().split())
                        resutlDict[num]['amount'] = matchAmount.group()
                        resutlDict[num]['date'] = date
                    conn = create_connection(database)
                    with conn:
                        print("connection created")
                        # Date, Amount, Category, Sub Category, Payment Method, Description, 
                        # Ref/Check No, Payee / Payer, Status, Receipt Picture, Account, Tag, Tax, Mileage
                        # create a new project
                        finalPayee = " ".join(matchPayeeName.group().split())
                        # knownPayee = [value for key, value in definedPayees.items() if value in finalPayee]
                        # knownCategory = [key for key, value in definedPayees.items() if value in finalPayee]
                        knownPayee = [payee for category,subcategory in definedPayees.items() for subc, payees in subcategory.items() for payee in payees if payee.lower() in finalPayee.lower()]
                        knownCategory = [category for category,subcategory in definedPayees.items() for subc, payees in subcategory.items() for payee in payees if payee.lower() in finalPayee.lower()]
                        knownSubcategory = [subc for category,subcategory in definedPayees.items() for subc, payees in subcategory.items() for payee in payees if payee.lower() in finalPayee.lower()]
                        if len(knownPayee) > 0:
                            finalPayee = knownPayee[0]
                        if len(knownCategory) > 0:
                            category = knownCategory[0]
                        else:
                            category = 'Unknown'
                        if len(knownSubcategory) > 0:
                            subCategory = knownSubcategory[0]
                        else:
                            subCategory = 'Unknown'
                        expense = (date, "-"+str(matchAmount.group()), category, subCategory, 'Debit', '', '', finalPayee,
                        'Cleared', '', 'Personal Expense', '', '', '')
                        create_project(conn, expense)
                        print('Task completed')
                else: 
                    print("Regex search failed")

        except Exception as e:
            print("Exception", e)

    else:
        print("No Internet connection")