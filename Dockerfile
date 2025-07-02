FROM node:18 AS builder

RUN apt-get update && apt-get install -y curl
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && apt-get install -y nodejs

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run lint && npm run type-check

RUN npm run build

FROM python:3.12

RUN apt-get update && \
    apt-get install -y ffmpeg curl gnupg apt-transport-https && \
    curl -sSL https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl -sSL https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-server.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y mssql-server

WORKDIR /app

COPY . /app
COPY --from=builder /static /app/static

RUN ls -al /app
RUN ls -al /app/static

ARG PYTHON_ENV=/app/venv
ENV VIRTUAL_ENV=$PYTHON_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN python -m venv $VIRTUAL_ENV && \
    . $VIRTUAL_ENV/bin/activate && \
    pip install --upgrade pip && \
    pip install --requirement requirements.txt

RUN chmod +x /app/startup.sh

ENV SA_PASSWORD="YourS3cureP@ssword!"
ENV MSSQL_PID="Developer"

EXPOSE 8000
CMD ["/bin/sh", "/app/startup.sh"]
