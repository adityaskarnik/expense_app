#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "expense" --dbname Expenses <<-EOSQL
    CREATE SCHEMA Expenses;
    SET search_path to Expenses;
	CREATE USER expense;
	CREATE DATABASE Expenses;
    ALTER DATABASE Expenses OWNER TO expense;
    ALTER USER expense WITH PASSWORD "${POSTGRES_PASSWORD}";
    CREATE TABLE IF NOT EXISTS Expenses ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, 
        "date" varchar(500) NOT NULL, "amount" varchar(500) NOT NULL, "category" varchar(500) NOT NULL, 
        "sub_category" varchar(500) NOT NULL, "payment_method" varchar(500) NOT NULL, 
        "description" varchar(500) NOT NULL, "ref_checkno" varchar(500) NOT NULL, 
        "payee_payer" varchar(500) NOT NULL, "status" varchar(500) NOT NULL, 
        "receipt_picture" varchar(500) NOT NULL, "account" varchar(500) NOT NULL, 
        "tag" varchar(500) NOT NULL, "tax" varchar(500) NOT NULL, "mileage" varchar(500) NOT NULL);
EOSQL