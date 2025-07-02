FROM node:18 AS builder

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run lint && npm run type-check
RUN npm run build

FROM python:3.12

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
