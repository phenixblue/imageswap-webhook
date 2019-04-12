FROM python:3

LABEL maintainer=joe@twr.io

COPY . /app
WORKDIR /app

RUN pip install pipenv

RUN pipenv install --system --deploy

CMD ["python", "hello.py"]
