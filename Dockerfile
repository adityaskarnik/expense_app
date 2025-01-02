FROM python:3.12.3

LABEL maintainer="Aditya Karnik aditya.s.karnik@gmail.com"

RUN apt-get update && apt-get install -y \
    build-essential \
    libyaml-dev \
    libssl-dev \
    libffi-dev \
    python3-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/

WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 8100