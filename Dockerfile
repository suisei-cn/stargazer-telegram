FROM python:3.8.2-slim

MAINTAINER LightQuantum

WORKDIR /app

RUN pip install --upgrade pip

COPY ./requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

RUN pip install sentry_sdk

COPY stargazer-tg ./stargazer-tg

CMD ["python", "-m", "stargazer-tg"]
