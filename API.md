# API Documentation - Coqui TTS Service

## Base URL
```
http://localhost:5000
```

## Table of Contents
- [Text-to-Speech Endpoints](#text-to-speech-endpoints)
- [Speaker Management Endpoints](#speaker-management-endpoints)
- [Models and Configuration](#models-and-configuration)

---

## Text-to-Speech Endpoints

### GET /
Главная страница веб-интерфейса для синтеза речи.

**Response:** HTML страница

---

### POST /synthesize
Синтез речи из текста.

**Content-Type:** `multipart/form-data`

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| text | string | Yes | - | Текст для синтеза (макс. 1000 символов) |
| model_id | string | No | xtts-v2 | ID модели (`xtts-v2`, `tacotron-en`, `tacotron-ru`) |
| language | string | No | en | Код языка (зависит от модели) |
| speaker | string | No | null | ID спикера для XTTS v2 |
| fmt | string | No | wav | Формат аудио (`wav` или `mp3`) |

**Example Request:**
```bash
curl -X POST http://localhost:5000/synthesize \
  -F "text=Hello, this is a test" \
  -F "model_id=xtts-v2" \
  -F "language=en" \
  -F "speaker=female-1" \
  -F "fmt=wav" \
  --output output.wav
```

**Response:** Audio file (WAV or MP3)

**Error Responses:**
- `400 Bad Request` - Invalid parameters
- `500 Internal Server Error` - Synthesis failed

---

### GET /speakers/{model_id}
Получение списка доступных спикеров для указанной модели.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| model_id | string | ID модели |

**Example Request:**
```bash
curl http://localhost:5000/speakers/xtts-v2
```

**Example Response:**
```json
{
  "speakers": [
    "female-1",
    "male-1",
    "female-2",
    "male-2",
    "my-custom-voice"
  ]
}
```

---

### GET /download/{filename}
Скачивание ранее сгенерированного аудиофайла из кэша.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| filename | string | Имя файла |

**Example Request:**
```bash
curl http://localhost:5000/download/abc123.wav --output audio.wav
```

**Response:** Audio file

**Error Responses:**
- `404 Not Found` - File not found

---

## Speaker Management Endpoints

### GET /speakers
Страница управления спикерами (веб-интерфейс).

**Response:** HTML страница

---

### POST /api/speakers
Создание нового спикера из аудиофайла.

**Content-Type:** `multipart/form-data`

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| speaker_id | string | Yes | Уникальный ID спикера (только буквы, цифры, дефисы, подчеркивания) |
| audio | file | Yes | Аудиофайл (WAV, MP3, FLAC) 3-10 секунд |

**Example Request:**
```bash
curl -X POST http://localhost:5000/api/speakers \
  -F "speaker_id=my-voice" \
  -F "audio=@sample.wav"
```

**Example Response:**
```json
{
  "success": true,
  "speaker": {
    "speaker_id": "my-voice",
    "path": "/app/speaker_samples/my-voice.wav",
    "is_default": false
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid speaker_id or trying to overwrite default speaker
- `500 Internal Server Error` - File save failed

---

### GET /api/speakers
Получение списка всех спикеров (дефолтных и пользовательских).

**Example Request:**
```bash
curl http://localhost:5000/api/speakers
```

**Example Response:**
```json
{
  "speakers": [
    {
      "speaker_id": "female-1",
      "label": "Female Voice 1",
      "is_default": true
    },
    {
      "speaker_id": "male-1",
      "label": "Male Voice 1",
      "is_default": true
    },
    {
      "speaker_id": "my-voice",
      "label": "My Voice",
      "is_default": false
    }
  ]
}
```

---

### GET /api/speakers/{speaker_id}
Получение информации о конкретном спикере.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| speaker_id | string | ID спикера |

**Example Request:**
```bash
curl http://localhost:5000/api/speakers/female-1
```

**Example Response:**
```json
{
  "speaker_id": "female-1",
  "label": "Female Voice 1",
  "is_default": true
}
```

**Error Responses:**
- `404 Not Found` - Speaker not found

---

### DELETE /api/speakers/{speaker_id}
Удаление пользовательского спикера.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| speaker_id | string | ID спикера |

**Example Request:**
```bash
curl -X DELETE http://localhost:5000/api/speakers/my-voice
```

**Example Response:**
```json
{
  "success": true,
  "message": "Speaker my-voice deleted"
}
```

**Error Responses:**
- `400 Bad Request` - Cannot delete default speaker
- `404 Not Found` - Speaker not found
- `500 Internal Server Error` - Delete failed

---

### GET /api/speakers/{speaker_id}/audio
Получение reference audio файла спикера.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| speaker_id | string | ID спикера |

**Example Request:**
```bash
curl http://localhost:5000/api/speakers/female-1/audio --output speaker.wav
```

**Response:** WAV audio file

**Error Responses:**
- `404 Not Found` - Speaker audio not found

---

## Models and Configuration

### Supported Models

#### XTTS v2 (Multilingual)
- **ID:** `xtts-v2`
- **Languages:** en, ru, de, es, fr, it, pt, pl, tr, ko, nl, cs, ar, zh-cn, ja, hu
- **Features:** Voice cloning, high quality, multilingual
- **Requires:** speaker_id (reference audio)

#### Tacotron 2 (English)
- **ID:** `tacotron-en`
- **Languages:** en
- **Model:** tts_models/en/ljspeech/tacotron2-DDC

#### Tacotron 2 (Russian)
- **ID:** `tacotron-ru`
- **Languages:** ru
- **Model:** tts_models/ru/mai/tacotron2

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 5000 | Server port |
| CACHE_TTL_SECONDS | 86400 | Cache TTL (24 hours) |
| MAX_TEXT_LENGTH | 1000 | Maximum text length |
| USE_GPU | 0 | Enable GPU (1) or CPU (0) |
| COQUI_TOS_AGREED | 1 | Accept Coqui TTS license |
| XDG_DATA_HOME | /app/data | Models storage directory |

### Audio Formats

**Supported Input Formats (for speaker creation):**
- WAV
- MP3
- FLAC

**Supported Output Formats (for synthesis):**
- WAV (default)
- MP3

### Rate Limits

Currently no rate limits are enforced. For production use, implement rate limiting middleware.

### Error Handling

All endpoints return JSON error responses in the following format:

```json
{
  "detail": "Error message description"
}
```

Common HTTP status codes:
- `200 OK` - Success
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Usage Examples

### Complete Workflow: Create Speaker and Synthesize

```bash
# 1. Create a new speaker
curl -X POST http://localhost:5000/api/speakers \
  -F "speaker_id=john-voice" \
  -F "audio=@john_sample.wav"

# 2. List all speakers to verify
curl http://localhost:5000/api/speakers

# 3. Synthesize speech with the new speaker
curl -X POST http://localhost:5000/synthesize \
  -F "text=Hello, this is my custom voice" \
  -F "model_id=xtts-v2" \
  -F "language=en" \
  -F "speaker=john-voice" \
  -F "fmt=mp3" \
  --output john_speech.mp3

# 4. Download the speaker's reference audio
curl http://localhost:5000/api/speakers/john-voice/audio \
  --output john_reference.wav

# 5. Delete the speaker when done
curl -X DELETE http://localhost:5000/api/speakers/john-voice
```

### Multilingual Synthesis

```bash
# English
curl -X POST http://localhost:5000/synthesize \
  -F "text=Hello world" \
  -F "model_id=xtts-v2" \
  -F "language=en" \
  -F "speaker=female-1" \
  --output en.wav

# Russian
curl -X POST http://localhost:5000/synthesize \
  -F "text=Привет мир" \
  -F "model_id=xtts-v2" \
  -F "language=ru" \
  -F "speaker=female-1" \
  --output ru.wav

# German
curl -X POST http://localhost:5000/synthesize \
  -F "text=Hallo Welt" \
  -F "model_id=xtts-v2" \
  -F "language=de" \
  -F "speaker=male-1" \
  --output de.wav
```

---

## Notes

- **Speaker Audio Quality:** For best results, use clean audio samples (3-10 seconds) without background noise
- **Text Length:** Long texts are automatically split into chunks and concatenated
- **Caching:** Synthesized audio is cached for 24 hours by default
- **Model Download:** Models are downloaded automatically on first use and stored in `/app/data/tts`
- **Speaker Storage:** Custom speakers are stored in `/app/speaker_samples`
