import imaplib
import re
from sys import getsizeof
import socket
import psycopg2
import os
from datetime import datetime
from celery import Celery
from celery.schedules import crontab

app = Celery('mail_checker',
            broker='amqp://rabbitmq:rabbitmq@rabbitmq:5672//')

from elasticsearch import Elasticsearch
index_name = 'expense_mail_checker'
doc_type = 'mailchecker'
es = Elasticsearch('elastic:' + os.environ['ELASTIC_PASSWORD'] + '@elasticsearch:9200/')

cwd = os.getcwd()

definedPayees = {'Food': {'Restaurant' : ['Zomato', 'CureFit', 'Diverse Retails', 'ONE97']}, 
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
    # sender.add_periodic_task(crontab(hour='*/1'),mail_checker.s())
    sender.add_periodic_task(crontab(minute='*'),mail_checker.s())

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

def insert_expense(conn, expense):
    sql = ''' INSERT INTO "Expenses"(date,amount,category,sub_category,payment_method,description,ref_checkno,payee_payer,status,receipt_picture,account,tag,tax,mileage) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) '''
    cur = conn.cursor()
    cur.execute(sql, expense)
    return cur.lastrowid

@app.task
def mail_checker():
    if (is_connected()):
        print('Process started')
        # global regex pattern for the getting payee name from mail
        regexPayeeName = r"((?<=PCA:[0-9]{10}:).*(?=Available))|((?<=(to|To)):?[0-9a-zA-Z.\s@\/]+((?=UTRNO)|(?=Available)))|((?<=at).*(?=txn))"
        regexAmount = r"((?<=INR\s).*(?=\sDebited))|(?<=INR\s).*(?=\shas)|((?<=Rs).*(?=\son))"
        regexDate = r"((?<=;).*\n?.*(?=\+0530))|((?<=Date:).*\n?.*(?<=(AM)|(PM)))|([0-9]{0,2}-[A-Z]{0,3}-[0-9]{0,4}\s[0-9]+?:[0-9]+?:[0-9]+)"
        mail = imaplib.IMAP4_SSL('imap.gmail.com')

        login = mail.login('budget.expenseapp@gmail.com', os.environ["BUDGET_PASSWORD"])

        mail.select("inbox")
        resutlDict = {}
        result, data = mail.search(None, '(UNSEEN)', '((OR HEADER Subject "Transaction alert for your State Bank of India Debit Card" HEADER Subject "Debit Alert"))')
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

                    if (matchPayeeName is None):
                        continue

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
                            try:
                                date = datetime.strptime(matchDate.group().split()[0],'%d-%b-%y').strftime('%Y/%m/%d')
                            except:
                                dd = ' '.join(matchDate.group().split()).replace(',','')
                                date = datetime.strptime(dd,'%a %d %b %Y %H:%M:%S').strftime('%Y/%m/%d')
                        resutlDict[num]['payee'] = " ".join(matchPayeeName.group().split())
                        resutlDict[num]['amount'] = matchAmount.group()
                        resutlDict[num]['date'] = date
                    connection = psycopg2.connect(user = "expense",
                                    password = os.environ["POSTGRES_PASSWORD"],
                                    host = "expense_db",
                                    port = "5432",
                                    database = "Expenses")
                    with connection:
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
                        expense = (date,float(("-"+str(matchAmount.group().replace(',',''))).lstrip('-')), category, subCategory, 'Debit', '', '', finalPayee,
                        'Cleared', '', 'Personal Expense', '', '', '')
                        expense = {}
                        expense['date'] = date
                        expense['amount'] = float(("-"+str(matchAmount.group().replace(',',''))).lstrip('-'))
                        expense['category'] = category
                        expense['sub_category'] = subCategory
                        expense['payment_method'] = 'Debit'
                        expense['description'] = ''
                        expense['ref_checkno'] = ''
                        expense['payee_payer'] = finalPayee
                        expense['status'] = 'Cleared'
                        expense['receipt_picture'] = ''
                        expense['account'] = 'Personal Expense'
                        expense['tag'] = ''
                        expense['tax'] = ''
                        expense['mileage'] = ''
                        es.index(index=index_name, doc_type=doc_type, body=expense)
                        insert_expense(connection, expense)
                        print('Task completed')
                else: 
                    print("Regex search failed")

        except Exception as e:
            print("Exception", e)

    else:
        print("No Internet connection")