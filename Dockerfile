FROM node:22-alpine AS frontend-builder

WORKDIR /web

COPY src/DairyOS.Web/package.json src/DairyOS.Web/package-lock.json ./
RUN npm ci

COPY src/DairyOS.Web/ ./
RUN npm run typecheck && npm run build


FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt


FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONPATH="/app/src"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local

COPY . .
COPY --from=frontend-builder /web/dist /app/src/DairyOS.Web/dist

EXPOSE 8000

CMD ["python", "-m", "dairyos.server", "--runtime-mode", "hosted", "--host", "0.0.0.0", "--port", "8000"]
