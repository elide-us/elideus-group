# syntax=docker/dockerfile:1.4

FROM node:18 AS builder

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run lint && npm run type-check
RUN npm run build

# ---- Final stage ----
FROM python:3.12-ubuntu22.04  # ✅ Use Ubuntu base so MSSQL can be installed

ARG MSSQL_PID
ARG ACCEPT_EULA

# Install prerequisites
RUN apt-get update && apt-get install -y \
    curl gnupg ffmpeg apt-transport-https software-properties-common

# Register the Microsoft SQL Server repo (✅ official method)
RUN curl -fsSL -o packages-microsoft-prod.deb \
    https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb

# Install SQL Server
RUN apt-get update && \
    ACCEPT_EULA=$ACCEPT_EULA apt-get install -y mssql-server

# Configure SQL Server securely
RUN --mount=type=secret,id=MSSQL_ADMIN_PASSWORD \
    export SA_PASSWORD=$(cat /run/secrets/MSSQL_ADMIN_PASSWORD) && \
    MSSQL_PID=$MSSQL_PID ACCEPT_EULA=$ACCEPT_EULA \
    /opt/mssql/bin/mssql-conf -n setup-sa

# Your app
WORKDIR /app

COPY . /app
COPY --from=builder /frontend/dist /app/static  # Adjusted path from /static to /frontend/dist

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
