# ------------------- Base image -------------------
ARG BASE_IMAGE=python:3.8-slim
ARG DOCKER_HUb=docker.arvancloud.ir

FROM ${DOCKER_HUb}/${BASE_IMAGE}
# ------------------- Metadata -------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on
# ------------------- Create app directory -------------------
WORKDIR /app
# ------------------- System deps -------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
 && rm -rf /var/lib/apt/lists/*
# ------------------- Python deps -------------------
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .

RUN python manage.py collectstatic --noinput || true
# ------------------- Entrypoint -------------------
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
