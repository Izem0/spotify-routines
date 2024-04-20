FROM python:3.12.0-slim-bullseye

RUN apt-get update && \
    apt-get install -y --no-install-recommends netcat && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

COPY poetry.lock pyproject.toml ./

RUN pip install poetry==1.8.2 && \
    poetry config virtualenvs.in-project true && \
    poetry install --no-root

COPY . ./

CMD poetry run python routine_get_new_albums.py