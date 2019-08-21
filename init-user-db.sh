#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "expense" --dbname "Expenses" <<-EOSQL
	CREATE USER expense;
	CREATE DATABASE Expenses;
    ALTER DATABASE Expenses OWNER TO expense;
    ALTER USER expense WITH PASSWORD 'EM@root';
EOSQL