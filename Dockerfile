FROM ubuntu:18.04

MAINTAINER hoparkgo9ma <me@ho9.me>

ADD . /app

WORKDIR /app

RUN apt update && apt install -y --no-install-recommends python3 python3-dev python3-pip python3-setuptools
RUN python3 -m pip install pip --upgrade && python3 -m pip install -r requirements.txt

EXPOSE 2500
CMD python3 app.py
