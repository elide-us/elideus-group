# ────────────────────────────────────────────────────────────────────────────────
# Frontend build
# ────────────────────────────────────────────────────────────────────────────────
FROM node:18 AS builder

# Download and install Node 18
RUN apt-get update && apt-get install -y curl python3 python3-pip python3-venv
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && apt-get install -y nodejs
WORKDIR /app

COPY requirements.txt ./

ARG PYTHON_ENV=/app/venv
ENV VIRTUAL_ENV=$PYTHON_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN python3 -m venv $VIRTUAL_ENV \
 && $VIRTUAL_ENV/bin/pip install --upgrade pip \
 && $VIRTUAL_ENV/bin/pip install -r requirements.txt

COPY . .

RUN python3 scripts/generate_rpc_library.py && python3 scripts/generate_rpc_client.py

WORKDIR /app/frontend

RUN npm ci
RUN npm run build





# ────────────────────────────────────────────────────────────────────────────────
# Python build
# ────────────────────────────────────────────────────────────────────────────────
FROM python:3.12

# RUN apt-get update && apt-get install -y ffmpeg libodbc2 unixodbc

# Install FOSS prereqs
RUN apt-get update && apt-get install -y curl gnupg2 ca-certificates apt-transport-https

# Register Microsoft repo the 2025-safe way:
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
      > /etc/apt/sources.list.d/mssql-release.list

# Now install
RUN apt-get update \
 && ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc libodbc2 ffmpeg \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only what we need from builder & runtime deps from tester
COPY --from=builder /app/static /app/static
COPY requirements.txt ./

# Configure the Python environment
ARG PYTHON_ENV=/app/venv
ENV VIRTUAL_ENV=$PYTHON_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install packages in Python environment
RUN python -m venv $VIRTUAL_ENV \
 && pip install --upgrade pip \
 && pip install -r requirements.txt

COPY . /app

# Run cleanup script to ensure efficient docker image
RUN chmod +x /app/docker_cleanup.sh \
 && /app/docker_cleanup.sh
 
RUN rm /app/docker_cleanup.sh

RUN chmod +x /app/startup.sh

# Informative log output of RPC namespace
RUN ls -al /app
RUN ls -Ral /app/rpc

# Setup dockerfile entry point
EXPOSE 8000
CMD ["/bin/sh", "/app/startup.sh"]
