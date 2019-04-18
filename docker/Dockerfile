FROM python:3-alpine

LABEL maintainer=joe@twr.io

COPY . /app
WORKDIR /app

RUN apk add ca-certificates && rm -rf /var/cache/apk/*

RUN pip install pipenv

RUN pipenv install --system --deploy

CMD ["python", "hello.py"]
