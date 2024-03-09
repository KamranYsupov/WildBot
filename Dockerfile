FROM python:3.10

COPY requirements.txt /temp/requirements.txt
COPY . /backend
WORKDIR /backend

RUN pip install --upgrade pip

RUN pip install -r /temp/requirements.txt

