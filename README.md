# Coqui TTS API (FastAPI)

Простой TTS‑сервис на базе Coqui TTS. Поддерживает CPU и GPU сборки.

**Порт:** 5000  
**Кэш аудио:** 24 часа  
**Максимальная длина текста:** 1000 символов  
**Форматы:** wav, mp3

## Быстрый старт (локально)

1. Создайте виртуальное окружение и установите зависимости:

```bash
python3 -m venv .venv
source .venv/bin/activate  # На Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. Запустите приложение:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 5000
```

3. Откройте [http://localhost:5000](http://localhost:5000)

## Docker

По умолчанию собирается CPU‑образ. Для GPU указывайте ARG `BUILD_FOR_GPU=1` при сборке (Dockerfile делает условную логику). Убедитесь, что на хосте установлен nvidia‑runtime (или используйте соответствующий образ).

### Запуск через Docker

```bash
# Сборка
docker build -t aicomrad-tts-coqui-ai:cpu .

# Запуск (с сохранением моделей)
docker run --rm -p 5000:5000 \
  -v $(pwd)/models:/app/data \
  aicomrad-tts-coqui-ai:cpu
```

Модели будут скачиваться в папку `models/tts` на хосте и сохраняться между перезапусками.

### Пример сборки GPU:

```bash
docker build --build-arg BUILD_FOR_GPU=1 -t aicomrad-tts-coqui-ai:gpu .
docker run --rm --gpus all -p 5000:5000 aicomrad-tts-coqui-ai:gpu
```

### Docker Compose:

```bash
docker-compose up -d
```

> **Примечание:** чтобы сократить размер образа, можно заранее указать URL для колеса torch (TORCH_WHEEL_URL) или использовать официальные колеса. Для production рекомендуем собрать отдельные образы для CPU и GPU с оптимизированными зависимостями.

## Конфигурация

Настройка через переменные окружения:

* `PORT` - Порт сервера (по умолчанию: 5000)
* `CACHE_TTL_SECONDS` - Время жизни кэша в секундах (по умолчанию: 86400 = 24 часа)
* `MAX_TEXT_LENGTH` - Максимальная длина текста (по умолчанию: 1000)
* `USE_GPU` - Использовать GPU (0 или 1, по умолчанию: 0)

## API Endpoints

### GET /

Веб-интерфейс для синтеза речи.

### POST /synthesize

Синтез речи из текста.

**Параметры (form-data):**
- `text` (обязательный) - Текст для синтеза
- `model_id` (опционально) - ID модели ('xtts-v2', 'tacotron-en', 'tacotron-ru', по умолчанию: 'xtts-v2')
- `language` (опционально) - Язык (зависит от модели)
- `speaker` (опционально) - Имя спикера (для мульти-спикер моделей)
- `fmt` (опционально) - Формат аудио ('wav' или 'mp3', по умолчанию: 'wav')

**Пример с curl:**

```bash
curl -X POST http://localhost:5000/synthesize \
  -F "text=Hello world" \
  -F "model_id=xtts-v2" \
  -F "language=en" \
  --output output.wav
```

### GET /speakers/{model_id}

Получить список доступных спикеров для выбранной модели.

### GET /download/{filename}

Скачать ранее сгенерированный аудиофайл из кэша.

## Поддерживаемые языки и модели

### XTTS v2 (Multilingual)
- **ID**: `xtts-v2`
- **Языки**: en, ru, de, es, fr, it, pt, pl, tr, ko, nl, cs, ar, zh-cn, ja, hu
- **Особенности**: Клонирование голоса (требует speaker), высокое качество

### Tacotron 2 (English)
- **ID**: `tacotron-en`
- **Языки**: en
- **Модель**: tts_models/en/ljspeech/tacotron2-DDC

### Tacotron 2 (Russian)
- **ID**: `tacotron-ru`
- **Языки**: ru
- **Модель**: tts_models/ru/mai/tacotron2

## Структура проекта

```
aicomrad-tts-coqui-ai/
├── README.md
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── app/
│   ├── main.py              # FastAPI приложение
│   ├── tts_service.py       # обёртка вокруг Coqui TTS
│   ├── cache.py             # простое файловое кэширование с TTL
│   ├── utils.py             # разбиение текста, утилиты конвертации
│   ├── templates/
│   │   └── index.html       # фронтенд
│   └── static/
│       └── css/
│           └── style.css
└── models/                  # опционально: сюда можно сохранять скачанные модели
```

## Замечания и рекомендации

* **Модели.** В проекте показаны примеры `tts_models/*` из Coqui hub. При запуске TTS API подтянет модель автоматически. Для офлайн/повторного использования скачивайте модель заранее и кладите в `models/`.
* **Torch и CUDA.** Для GPU используйте соответствующие торч‑колёса (wheel) для вашей CUDA версии. В Dockerfile добавлен аргумент `TORCH_WHEEL_URL` чтобы переопределять URL колеса при сборке.
* **Оптимизация размера образа.** Для production можно: 1) использовать slim/mini wheels, 2) собирать в отдельном builder и копировать только site‑packages, 3) убирать ненужные пакеты.
* **Безопасность.** На проде замени UI на защищённую и добавь rate limiting, проверку входа и ограничения по длине/числу запросов.
* **Тесты.** Добавь unit‑тесты для split_text, cache и моков TTS.
# aicomrad-tts-coqui-ai
