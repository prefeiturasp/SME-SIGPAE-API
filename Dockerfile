FROM python:3.13.3-bullseye AS docs-builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc g++ git libpq-dev libmagic1 \
        libcairo2 libpango-1.0-0 libpangocairo-1.0-0 && \
    pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir pipenv==2023.11.15

WORKDIR /code
COPY . /code/

RUN pipenv install --system --deploy --ignore-pipfile --dev && \
    sphinx-build -b html docs/source docs/build/html

FROM python:3.13.3-bullseye

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev libmagic1 \
        libcairo2 libpango-1.0-0 libpangocairo-1.0-0 && \
    pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir pipenv==2023.11.15

WORKDIR /code
COPY . /code/

RUN pipenv install --system --deploy --ignore-pipfile && \
    rm -rf /var/lib/apt/lists/*

COPY --from=docs-builder /code/docs/build/html /code/docs/build/html

EXPOSE 8000