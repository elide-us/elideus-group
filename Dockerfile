# ────────────────────────────────────────────────────────────────────────────────
# Frontend build
# ────────────────────────────────────────────────────────────────────────────────
FROM node:18 AS builder

# Download and install Node 18
RUN apt-get update && apt-get install -y curl python3 python3-pip python3-venv
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && apt-get install -y nodejs
WORKDIR /app

ARG PYTHON_ENV=/app/venv
ENV VIRTUAL_ENV=$PYTHON_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN python3 -m venv $VIRTUAL_ENV \
 && $VIRTUAL_ENV/bin/pip install --upgrade pip \
 && $VIRTUAL_ENV/bin/pip install pydantic

COPY requirements.txt ./
RUN $VIRTUAL_ENV/bin/pip install -r requirements.txt

COPY . .

RUN python3 scripts/generate_rpc_library.py && python3 scripts/generate_rpc_client.py

WORKDIR /app/frontend

RUN npm ci
RUN npm run build





# ────────────────────────────────────────────────────────────────────────────────
# Python build
# ────────────────────────────────────────────────────────────────────────────────
FROM python:3.12

RUN apt-get update && apt-get install -y ffmpeg
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
