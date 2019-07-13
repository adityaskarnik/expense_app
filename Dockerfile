FROM python:3.7

MAINTAINER adityakarnik

COPY . /app/

WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 8100

CMD celery worker -A payee_name -l INFO --beat --concurrency=2 -n 'main_app'