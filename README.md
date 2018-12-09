## Importing json in database
### SQLITE3
As ``sqlite3`` only supports only csv, first convert the json file to csv from [here](https://json-csv.com/). Download and keep the csv

Check installation of sqlite3 is done, else do ``sudo apt install sqlite3``

Connect to database with:
```
sqlite3 db.sqlite3 #db.sqlite3 is your own database filename
```
<br>

```
.mode csv
.import data.csv table_name
```
Provide your own table name and the actual path to the csv file and with ``.import`` command you can load all the data from the csv to database with the same existing format of your json
<br>

With ``.tables`` you can  view the newly created table in sqlite
<br>
With ``.schema`` you can view the query for tables creation that will is used
<br>
Now to view you data has been successfully imported to json, run the query:
```
SELECT * FROM table_name
```
Here you will get the output. Now you have successfully imported the json in to sqlite3 database

<br>

### POSTGRES
First convert the json file to csv from [here](https://json-csv.com/). Download and keep the csv

Connect to Postgres:
```
sudo -i -u postgres
```
Once you have connected, run:
```
psql
```
Now first create a database, run:
```
CREATE DATABASE db_name;
```
Now create table with the same column names that are there in your json file.
```
CREATE TABLE expenses(id SERIAL PRIMARY KEY, date VARCHAR not null, amount VARCHAR not null, category VARCHAR not null, sub_category VARCHAR not null, payment_method VARCHAR not null, description VARCHAR not null, ref VARCHAR not null, payee_payer VARCHAR not null, status VARCHAR not null, receipt_picture VARCHAR not null, account VARCHAR not null, tag VARCHAR not null, tax VARCHAR not null, mileage VARCHAR not null);
```
> Note: Here in my json I do not have a id field, I have added it to give my table a default primary key which is and exception while doing the import

Next, view the created table with ``\dt`` in the terminal

Now the final and most important step to do is, match the column names with the json while inserting data, 
```
COPY expenses(date, amount, category, sub_category, payment_method, description, ref, payee_payer, status, receipt_picture, account, tag, tax, mileage) FROM 'data.csv' DELIMITER ',' CSV HEADER;
```
> Keeping in mind the table_name, here my table name is **expenses** 
> Input your full path to the csv while doing the import

Voila!!!
You have completed the import. Now, run
```
SELECT * FROM expenses
```
This will give the output of all your data in tables that you have imported


## Donation
If this page helps you reduce time to develop, you can give me a cup of coffee   :coffee:

[![paypal](https://cdn-images-1.medium.com/max/738/1*G95uyokAH4JC5Ppvx4LmoQ@2x.png)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=ZJM97M6KBLHZY)