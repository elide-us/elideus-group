# ────────────────────────────────────────────────────────────────────────────────
# Frontend build
# ────────────────────────────────────────────────────────────────────────────────
FROM node:18 AS builder

RUN apt-get update && apt-get install -y curl
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && apt-get install -y nodejs

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run lint && npm run type-check
RUN npm run build

# ────────────────────────────────────────────────────────────────────────────────
# Test stage
# ────────────────────────────────────────────────────────────────────────────────
FROM python:3.12 AS tester

# Install system deps and create venv
RUN apt-get update && apt-get install -y ffmpeg
WORKDIR /app

ARG PYTHON_ENV=/app/venv
ENV VIRTUAL_ENV=$PYTHON_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy only requirements; install both runtime and test deps
COPY requirements.txt requirements-dev.txt ./
RUN python -m venv $VIRTUAL_ENV \
 && pip install --upgrade pip \
 && pip install -r requirements.txt \
 && pip install -r requirements-dev.txt

# Copy your application code and tests
COPY . /app

# Verify layout
RUN ls -R /app

# Run the test suite
# Fails the build if any test fails
RUN pytest --maxfail=1 --disable-warnings -q

# ────────────────────────────────────────────────────────────────────────────────
# Final runtime image
# ────────────────────────────────────────────────────────────────────────────────
FROM python:3.12

RUN apt-get update && apt-get install -y ffmpeg
WORKDIR /app

# Copy only what we need from builder & runtime deps from tester
COPY --from=builder /static /app/static
COPY requirements.txt ./

ARG PYTHON_ENV=/app/venv
ENV VIRTUAL_ENV=$PYTHON_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN python -m venv $VIRTUAL_ENV \
 && pip install --upgrade pip \
 && pip install -r requirements.txt

# Copy application code (remove tests)
COPY . /app
RUN rm -rf /app/tests
# RUN rm -rf /app/scripts

# Verify layout
RUN ls -R /app

RUN chmod +x /app/startup.sh

EXPOSE 8000
CMD ["/bin/sh", "/app/startup.sh"]
