import os
import csv
import json
old_filename = '/home/adityakarnik/console_projects/expense_manager/expense_data.json'
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
        print("Exception",e)
        return None

def check_new_data(new_file):
    with open(old_filename) as d:        
        data = json.loads(d.read())
        out_file = convert_csv_to_json(new_file)
        if (out_file is not None):
            print("CSV File converted successfully to JSON")
            with open(out_file) as d_new:
                data_new = json.loads(d_new.read())
                if (len(data_new) > len(data)):
                    os.rename(old_filename, cwd+'/expense_data_old.json')
                    os.rename(out_file, cwd+'/expense_data.json')
                    print("Old file renamed and New file generated")
                    return (len(data_new) - len(data))
        return 0
            
# check_new_data(new)