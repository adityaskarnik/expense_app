import os
import csv
import json
old_filename = '/home/adityakarnik/console_projects/expense_manager/expense_data.json'
from dotenv import load_dotenv
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()
cwd = os.getcwd()

def convert_csv_to_json(file):
    try:
        outputJson = cwd+'/outJson.json'
        csv_rows = []
        with open(file ,'r') as csvfile:
            next(csvfile)
            reader = csv.DictReader(csvfile)
            title = reader.fieldnames
            for row in reader:
                csv_rows.extend([{title[i]:row[title[i]] for i in range(len(title))}])
                with open(outputJson, "w") as f:
                    f.write(json.dumps(csv_rows))
        return outputJson
    except Exception as e:
        logging.error(f"Exception: {e}")
        return None

def check_new_data(new_file):
    try:
        data = []
        logging.info(f"old_filename: {old_filename}")
        with open(old_filename) as d:
            if os.path.getsize(old_filename) > 0:
                data = json.load(d)
            else: data = []
            out_file = convert_csv_to_json(new_file)
            if (out_file is not None):
                logging.info("CSV File converted successfully to JSON")
                with open(out_file) as d_new:
                    data_new = json.loads(d_new.read())
                    logging.info(f"{len(data_new)},{len(data)}")
                    if (len(data_new) > len(data)):
                        os.rename(old_filename, cwd+'/expense_data_old.json')
                        os.rename(out_file, cwd+'/expense_data.json')
                        logging.info("Old file renamed and New file generated")
                        return (len(data_new) - len(data))
            return 0
    except Exception as e:
        logging.error("Exception in check_new_data", e)
        return 0
            
# check_new_data(new)

def download_new_attachment():
    import imaplib
    import re
    from sys import getsizeof
    import socket
    import os
    import email
    from datetime import datetime
    cwd = os.getcwd()
    
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    login = mail.login('budget.expenseapp@gmail.com', os.getenv("BUDGET_PASSWORD", ""))

    mail.select("inbox")
    resutlDict = {}
    result, data = mail.search(None, '(UNSEEN)', '(HEADER Subject "Manager.csv")')
    try:
        for num in data[0].split():
            latest_email_uid = num
            typ, data = mail.fetch(num, '(RFC822)')
            raw_email = data[0][1]
            resutlDict[num] = {}
            raw_email = raw_email.decode('utf-8')
            email_message = email.message_from_string(raw_email)
            for part in email_message.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue
                fileName = part.get_filename()
                if bool(fileName):
                    filePath = os.path.join("/tmp", fileName)
                    if not os.path.isfile(filePath) :
                        fp = open(filePath, 'wb')
                        fp.write(part.get_payload(decode=True))
                        fp.close()

                    subject = str(email_message).split("Subject: ", 1)[1].split("\nTo:", 1)[0]
                    logging.info('Downloaded "{file}" from email titled "{subject}" with UID {uid}.'.format(file=fileName, subject=subject, uid=latest_email_uid.decode('utf-8')))
                    return filePath
    except Exception as e:
        logging.error(f"EXCEPTION DOWNLOADING ATTACHMENTS: {e}")