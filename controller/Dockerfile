FROM python:3.11-buster

RUN apt-get update && apt-get -y install build-essential lirc

WORKDIR /opt/project

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY *.py .