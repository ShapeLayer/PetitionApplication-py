FROM python:3.6

MAINTAINER hoparkgo9ma <me@ho9.me>

ADD . /app

WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 2500
CMD python3 app.py
