import pandas as pd
import json

# Load JSON data
with open('expense_data.json', 'r') as json_file:
    data = json.load(json_file)

df = pd.DataFrame(data)

df.to_csv('data.csv', index=False)

print("JSON data has been converted to CSV and saved as 'data.csv'")