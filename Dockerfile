# Stage: base builder
ARG BUILD_FOR_GPU=0
FROM python:3.10-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive

# Установим системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  libsndfile1 \
  ffmpeg \
  git \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Скопируем требования и установим (в builder, чтобы кешировать)
WORKDIR /src
COPY requirements.txt ./

# Позволяет переопределить URL для колеса torch при сборке
ARG TORCH_WHEEL_URL=""

RUN pip install --upgrade pip setuptools wheel

RUN pip install --no-cache-dir -r requirements.txt

# Stage: runtime
FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
  libsndfile1 \
  ffmpeg \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем установленные пакеты из builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем приложение
COPY app ./app

# Копируем скрипт для создания speaker samples
COPY create_speaker_samples.py ./

# Создаём speaker samples для XTTS v2
RUN python create_speaker_samples.py && \
  mkdir -p /app/speaker_samples && \
  mv speaker_samples/* /app/speaker_samples/ || true

# Создаём директории для моделей и кэша
RUN mkdir -p /app/models /app/cache

ENV PORT=5000 \
  COQUI_TOS_AGREED=1 \
  XDG_DATA_HOME=/app/data

# Создаём директорию для данных (модели будут в /app/data/tts)
RUN mkdir -p /app/data

EXPOSE 5000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
