FROM python:3.7

MAINTAINER adityakarnik

COPY . /app/

WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 8100