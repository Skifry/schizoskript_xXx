FROM python:3.7

WORKDIR /app/
RUN pip install poetry

ADD ./pyproject.toml /app/
ADD ./poetry.lock /app/

RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi

ADD rsinterpreter /app/rsinterpreter
ADD main.py /app/
