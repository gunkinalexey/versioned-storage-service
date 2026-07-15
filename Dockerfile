FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=off

WORKDIR /opt

COPY ./pyproject.toml .
COPY ./src ./src
COPY ./data ./data

RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.in-project true
RUN poetry install --only main --no-interaction --no-ansi

EXPOSE 8000

ENTRYPOINT ["poetry", "run", "python", "src/main.py"]
