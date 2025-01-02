import imaplib
import re
from sys import getsizeof
import socket
import psycopg2
import os
from datetime import datetime
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
import logging
from elasticsearch import Elasticsearch

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging = logging.getLogger(__name__)

load_dotenv()

app = Celery('payee_name',
            broker='amqp://rabbitmq:rabbitmq@rabbitmq:5672//')

index_name = 'expense_mail_checker'
doc_type = 'mailchecker'
es = Elasticsearch(
    ['http://10.10.0.6:9200'],
    http_auth=('elastic', os.getenv('ELASTIC_PASSWORD', '')),
    headers={"Content-Type": "application/json"}
)


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
        logging.info('Internet check')
        return True
    except OSError:
        pass
    return False

def insert_expense(conn, expense):
    sql = ''' INSERT INTO "Expenses"(date, amount, category, sub_category, payment_method, description, ref_checkno, payee_payer, status, receipt_picture, account, tag, tax, mileage)
              VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) '''
    cur = conn.cursor()
    cur.execute(sql, expense)
    conn.commit()
    return cur.lastrowid

def parse_email(raw_email):
    def try_parse_email(email_content):
        regex_patterns_payee = [
            r"((?<=PCA:[0-9]{10}:).*(?=Available))|((?<=(to|To)):?[0-9a-zA-Z.\s@\/]+((?=UTRNO)|(?=Available)))|((?<=at).*(?=txn))",
            r'<td>Terminal Owner Name<\/td>\s*<td id="bank">([^<]+)<\/td>',
            r"ATD:[0-9]{10}:[A-Z0-9]+:(.*?)(?=\. Available Balance on)",
            r"PCA:[0-9]{10}:[0-9]+:(.*?)(?=\s{2,})",
            r"(?<=PCA:[0-9]{10}:).*(?=Available)",
            r"(?<=to|To):?[0-9a-zA-Z.\s@\/]+(?=(UTRNO|Available))",
            r"NET TXN: (?:PAYU|AVENUES)\s[0-9]+",
            r"IMPS/NA/XXX[0-9]{4}/RRN:[0-9]+/[0-9]+/State Bank Of IndiaRD Mobile",
            r"[A-Z]{3}\sATM\s+[A-Z]+\s*\d{4}",
            r"(?=([0-9]+\sat\s))?([A-Z]{3}\sATM(\s{2})?(=?)([A-Z]+)?([0-9]+)?(=?)([A-Z]+)?([0-9]+)?\s?)([A-Z]+)?([0-9]+)?(?=\.)",
            r"on account of\s(.*)\n?\r?\.?(?=\sAvailable Balance)",
            r"w\/d\sat\s(.*)fm\sA\/cx",
            r'<td id="tranType">([A-Z]+\s?[A-Z]+)<\/td>'
        ]
        regex_patterns_amount = [
            r"(?<=INR\s)[\d,]+(?:\.\d{1,2})?(?=\sDebited)",
            r"(?<=INR\s)[\d,]+(?:\.\d{1,2})?(?=\shas)",
            r"Rs\s?([\d,]+(?:\.\d{1,2})?)(?=\son)",
            r'<td id="transactionNumber">(\d+)</td>.*?<td id="amount">([\d.]+)</td>',
            r"(?<=Amount:)\s*[\d,]+(?:\.\d{1,2})?",
            r"(?<=INR\s)[\d,]+(?:\.\d{1,2})?(?=\sDebited)|(?<=INR\s)[\d,]+(?:\.\d{1,2})?(?=\shas)|(?<=Rs\s)[\d,]+(?:\.\d{1,2})?(?=\son)",
            r"(?<=\s)[\d,]+(?=\swithdrawn)",
            r'<td>Amount \(INR\)<\/td>\s*<td id="amount">([\d,]+\.\d{1,2})<\/td>',
            r"Rs\s([\d,]+)\sw\/d"
        ]
        regex_patterns_date = [
            r'<td>Date &amp; Time</td>\s*<td id="dateTime">([A-Za-z]{3} \d{1,2}, \d{4}, \d{2}:\d{2})</td>',
            r"((?<=;).*\n?.*(?=\+0530))|((?<=Date:).*\n?.*(?<=(AM)|(PM)))|([0-9]{0,2}-[A-Z]{0,3}-[0-9]{0,4}\s[0-9]+?:[0-9]+?:[0-9]+)"
        ]

        matchPayeeName = None
        matchAmount = None
        matchDate = None

        try:
            for pattern in regex_patterns_payee:
                match = re.search(pattern, email_content)
                if match:
                    logging.info(f"Payee pattern matched: {match.group(2) if match.lastindex == 2 else match.group(1) if match.lastindex == 1 else match.group().strip()}")
                    matchPayeeName = match.group(2) if match.lastindex == 2 else match.group(1) if match.lastindex == 1 else match.group().strip()
                    if 'CASH WITHDRAWAL' in matchPayeeName:
                        return "CASH WITHDRAWAL", None, None
                    break

            for pattern in regex_patterns_amount:
                match = re.search(pattern, email_content)
                if match:
                    logging.info(f"Amount pattern matched: {match.group(2) if match.lastindex == 2 else match.group(1) if match.lastindex == 1 else match.group().strip()}")
                    matchAmount = match.group(2) if match.lastindex == 2 else match.group(1) if match.lastindex == 1 else match.group().strip()
                    break

            for pattern in regex_patterns_date:
                match = re.search(pattern, email_content)
                if match:
                    logging.info(f"Date pattern matched: {match.group(2) if match.lastindex == 2 else match.group(1) if match.lastindex == 1 else match.group().strip()}")
                    matchDate = match.group(2) if match.lastindex == 2 else match.group(1) if match.lastindex == 1 else match.group().strip()
                    break

            return matchPayeeName, matchAmount, matchDate
        except Exception as e:
            logging.error(f"Error parsing email: {e}")
            raise e

    try:
        logging.debug(f"DEBUG: trying for the first time")
        matchPayeeName, matchAmount, matchDate = try_parse_email(raw_email)
    except:
        logging.info("Trying with UTF-8 decoding")
        raw_email_utf8 = raw_email.decode('utf-8')
        matchPayeeName, matchAmount, matchDate = try_parse_email(raw_email_utf8)

    return matchPayeeName, matchAmount, matchDate


def format_date(matchDate):
    try:
        logging.info(f"Trying first way: {matchDate}")
        matchDate = matchDate.strip()
        date = datetime.strptime(matchDate.split()[0], '%d-%b-%Y').strftime('%Y/%m/%d')
        logging.info(f"format_date: {date}")
    except Exception as e:
        logging.error(f"Date format exception, trying another way: {e}")
        try:
            date = datetime.strptime(matchDate.split()[0], '%d-%b-%y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.error(f"Date format exception, trying next way: {e}")
            try:
                dd = ' '.join(matchDate.split()).replace(',', '')
                date = datetime.strptime(dd, '%a %d %b %Y %H:%M:%S').strftime('%Y/%m/%d')
            except Exception as e:
                try:
                    logging.info(f"Date format exception, trying second last way: {e}")
                    date_format = '%b %d, %Y, %H:%M'
                    parsed_date = datetime.strptime(matchDate, date_format)
                    date = parsed_date.strftime('%Y/%m/%d')
                except Exception as e:
                    logging.info(f"Date format exception, trying last way: {e}")
                    date_format = '%a, %b %d, %Y at %I:%M %p'
                    parsed_date = datetime.strptime(matchDate, date_format)
                    date = parsed_date.strftime('%Y/%m/%d')
    return date

@app.task
def mail_checker():
    if not is_connected():
        logging.error("No Internet connection")
        return

    logging.info('Process started')

    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        logging.info('Connected to Gmail')
        mail.login('budget.expenseapp@gmail.com', os.getenv("BUDGET_PASSWORD", ""))
        logging.info('Logged in')
        mail.select("inbox")
        logging.info('Inbox selected')

        result, data = mail.search(None, '(UNSEEN)', '((OR HEADER Subject "Transaction alert for your State Bank of India Debit Card" HEADER Subject "Debit Alert"))')
        logging.info(f"Mail search completed, found {len(data[0].split())}")

        for num in data[0].split():
            try:
                typ, data = mail.fetch(num, '(RFC822)')
                logging.info(f"Fetched mail {num}")
                raw_email = data[0][1]

                matchPayeeName, matchAmount, matchDate = parse_email(raw_email)
                logging.info(f"Matched payee: {matchPayeeName}, amount: {matchAmount}, date: {matchDate}")

                if matchPayeeName == "CASH WITHDRAWAL":
                    logging.info("Cash withdrawal email, skipping")
                    continue
                elif 'ATMs for better security, convenience & faster complaint resolution' in matchPayeeName:
                    logging.info("ATM Alert email, skipping")
                    continue
                elif not (matchAmount and matchDate and matchPayeeName):
                    logging.error("Regex search failed normally and after UTF-8 decoding")
                    mail.store(num, '-FLAGS', '\\Seen')
                    continue

                date = format_date(matchDate)
                amount_value = float(("-" + str(matchAmount.replace(',', ''))).lstrip('-'))
                finalPayee = " ".join(matchPayeeName.split())

                knownPayee = [finalPayee if payee.lower() == 'rent' and 'rent' in finalPayee.lower() else payee for category, subcategory in definedPayees.items() for subc, payees in subcategory.items() for payee in payees if payee.lower() in finalPayee.lower()]
                knownCategory = [category for category, subcategory in definedPayees.items() for subc, payees in subcategory.items() for payee in payees if payee.lower() in finalPayee.lower()]
                knownSubcategory = [subc for category, subcategory in definedPayees.items() for subc, payees in subcategory.items() for payee in payees if payee.lower() in finalPayee.lower()]

                category = knownCategory[0] if knownCategory else 'Unknown'
                subCategory = knownSubcategory[0] if knownSubcategory else 'Unknown'
                finalPayee = knownPayee[0] if knownPayee else finalPayee

                logging.info(f"Payee: {finalPayee}, Amount: {amount_value}, Date: {date}")
                expense = (date, amount_value, category, subCategory, 'Debit', '', '', finalPayee, 'Cleared', '', 'Personal Expense', '', '', '')

                expense_es = {
                    'date': date,
                    'amount': amount_value,
                    'category': category,
                    'sub_category': subCategory,
                    'payment_method': 'Debit',
                    'description': '',
                    'ref_checkno': '',
                    'payee_payer': finalPayee,
                    'status': 'Cleared',
                    'receipt_picture': '',
                    'account': 'Personal Expense',
                    'tag': '',
                    'tax': '',
                    'mileage': ''
                }

                conn = psycopg2.connect(
                    user = "expense",
                    password=os.getenv("POSTGRES_PASSWORD", ""),
                    host = "expense_db",
                    port = "5432",
                    database = "Expenses"
                )

                insert_expense(conn, expense)
                conn.close()
                logging.info(f"Inserted expense: {expense}")
                logging.info(f"Expense for Elasticsearch: {expense_es}")

                # Assuming you have an Elasticsearch client instance `es` and an index name `index_name`
                # try:
                #     es.index(index=index_name, body=expense_es)
                # except Exception as e:
                #     logging.error(f"Error inserting expense in Elasticsearch: {e}")


            except Exception as e:
                logging.error(f"Error processing email {num}: {e}")
                mail.store(num, '-FLAGS', '\\Seen')
            except CashWithdrawalException as e:
                pass

    except imaplib.IMAP4.error as e:
        logging.error(f"IMAP error: {e}")
    except Exception as e:
        logging.error(f"Exception in mail_checker: {e}")
