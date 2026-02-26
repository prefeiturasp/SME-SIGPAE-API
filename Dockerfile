FROM python:3.13.3-bullseye

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ git libpq-dev libmagic1 libcairo2 libpango-1.0-0 libpangocairo-1.0-0  && \
    pip install psycopg2-binary  && \
    pip install xlsxwriter && \
    pip install pycparser && \
    pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir pipenv==2023.11.15

WORKDIR /code
COPY . /code/

RUN pipenv install --system --deploy --ignore-pipfile && \
    apt-get remove -y gcc g++ git && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 8000
