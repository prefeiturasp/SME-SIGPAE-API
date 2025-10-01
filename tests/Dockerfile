FROM node:16

RUN apt-get update && apt-get install -y \
    xvfb \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libgtk-3-0 \
    libgbm1 \
    libasound2 \
    libxcomposite1 \
    libxrandr2 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libpango1.0-0 \
    fonts-liberation \
    libappindicator3-1 \
    libxss1 \
    lsb-release \
    wget \
    xdg-utils

RUN mkdir -p /SME-SIGPAE-POC-TESTES

WORKDIR /SME-SIGPAE-POC-TESTES

COPY package*.json /SME-SIGPAE-POC-TESTES/

RUN npm install

COPY . /SME-SIGPAE-POC-TESTES

CMD ["xvfb-run", "npx", "cypress", "run"]
