# syntax=docker/dockerfile:1.4

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
ARG MSSQL_PID
ARG ACCEPT_EULA

# RUN apt-get update && apt-get install -y ffmpeg
RUN apt-get update && apt-get install -y ffmpeg curl gnupg apt-transport-https

#RUN curl -sSL https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
#RUN curl -sSL https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-server.list

#RUN apt-get update && ACCEPT_EULA=$ACCEPT_EULA apt-get install -y mssql-server

# Modern GPG key setup
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
  | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg

RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] \
  https://packages.microsoft.com/debian/12/prod bookworm main" \
  > /etc/apt/sources.list.d/mssql-server.list

RUN apt-get update && ACCEPT_EULA="${ACCEPT_EULA}" \
    apt-get install -y mssql-server

# mssql-conf setup step
RUN --mount=type=secret,id=MSSQL_ADMIN_PASSWORD \
    export SA_PASSWORD=$(cat /run/secrets/MSSQL_ADMIN_PASSWORD) && \
    MSSQL_PID=$MSSQL_PID ACCEPT_EULA=$ACCEPT_EULA /opt/mssql/bin/mssql-conf -n setup-sa

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

EXPOSE 8000
CMD ["/bin/sh", "/app/startup.sh"]
