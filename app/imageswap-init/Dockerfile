FROM python:3.8.12-alpine3.15

LABEL maintainer=joe@twr.io

COPY ./Pipfile* /app/

WORKDIR /app

RUN apk add --update --no-cache bind-tools ca-certificates gcc musl-dev python3-dev libffi-dev openssl-dev

RUN pip install pipenv

RUN pipenv install --system --deploy

RUN apk del gcc musl-dev python3-dev libffi-dev openssl-dev

COPY ./imageswap-init.py /app/

CMD ["python", "imageswap-init.py"]