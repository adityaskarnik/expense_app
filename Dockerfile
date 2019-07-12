FROM python:3.7-alpine

COPY ./expense_app /app
WORKDIR /app

RUN pip install -r requirements.txt

CMD python manage.py runserver 0.0.0.0:8100