# Stage: base builder
ARG BUILD_FOR_GPU=0

# Условные base images
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04 AS base-gpu
FROM python:3.10-slim AS base-cpu

# Выбираем base в зависимости от BUILD_FOR_GPU
FROM base-cpu AS base-0
FROM base-gpu AS base-1

# Builder stage
FROM base-${BUILD_FOR_GPU} AS builder

# Переопределяем ARG для этого stage
ARG BUILD_FOR_GPU=0
ENV DEBIAN_FRONTEND=noninteractive

# Для GPU образа устанавливаем Python 3.10 и pip
RUN if [ "${BUILD_FOR_GPU}" = "1" ]; then \
  apt-get update && \
  apt-get install -y --no-install-recommends \
  python3.10 \
  python3-pip \
  python3.10-dev && \
  ln -sf /usr/bin/python3.10 /usr/bin/python && \
  ln -sf /usr/bin/python3.10 /usr/bin/python3 && \
  ln -sf /usr/bin/pip3 /usr/bin/pip && \
  rm -rf /var/lib/apt/lists/*; \
  fi

# Установим системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  libsndfile1 \
  ffmpeg \
  git \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Скопируем требования и установим
WORKDIR /src
COPY requirements.txt ./

# Обновляем pip
RUN python -m pip install --upgrade pip setuptools wheel

# Установка PyTorch с правильной версией (GPU или CPU)
RUN if [ "${BUILD_FOR_GPU}" = "1" ]; then \
  python -m pip install --no-cache-dir \
  torch==2.1.2 \
  torchaudio==2.1.2 \
  --index-url https://download.pytorch.org/whl/cu118; \
  else \
  python -m pip install --no-cache-dir \
  torch==2.1.2 \
  torchaudio==2.1.2; \
  fi

# Установка остальных зависимостей
RUN python -m pip install --no-cache-dir -r requirements.txt || true

# Runtime stage
FROM base-cpu AS runtime-0
FROM base-gpu AS runtime-1
FROM runtime-${BUILD_FOR_GPU} AS runtime

# Переопределяем ARG для runtime stage
ARG BUILD_FOR_GPU=0
ENV DEBIAN_FRONTEND=noninteractive

# Для GPU образа устанавливаем Python 3.10
RUN if [ "${BUILD_FOR_GPU}" = "1" ]; then \
  apt-get update && \
  apt-get install -y --no-install-recommends \
  python3.10 \
  python3-pip && \
  ln -sf /usr/bin/python3.10 /usr/bin/python && \
  ln -sf /usr/bin/python3.10 /usr/bin/python3 && \
  ln -sf /usr/bin/pip3 /usr/bin/pip && \
  rm -rf /var/lib/apt/lists/*; \
  fi

# Установим runtime зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
  libsndfile1 \
  ffmpeg \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем установленные пакеты из builder
# Для CPU (Debian): /usr/local/lib/python3.10/site-packages
# Для GPU (Ubuntu): /usr/local/lib/python3.10/dist-packages или site-packages
COPY --from=builder /usr/local/lib/python3.10/ /usr/local/lib/python3.10/
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем приложение
COPY app ./app

# Копируем скрипт для создания speaker samples
COPY create_speaker_samples.py ./
COPY check_gpu.py ./

# Создаём speaker samples для XTTS v2
RUN python create_speaker_samples.py && \
  mkdir -p /app/speaker_samples && \
  mv speaker_samples/* /app/speaker_samples/ || true

# Создаём директории для моделей и кэша
RUN mkdir -p /app/models /app/cache /app/data

# Устанавливаем переменные окружения
ENV PORT=5000 \
  COQUI_TOS_AGREED=1 \
  XDG_DATA_HOME=/app/data \
  USE_GPU=${BUILD_FOR_GPU} \
  PRELOAD_MODEL=xtts-v2

EXPOSE 5000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
