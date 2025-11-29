from fastapi import FastAPI, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from .tts_service import TTSService
from .cache import FileCache
from .utils import split_text

PORT = int(os.getenv('PORT', 5000))
CACHE_TTL = int(os.getenv('CACHE_TTL_SECONDS', 86400))
MAX_TEXT_LENGTH = int(os.getenv('MAX_TEXT_LENGTH', 1000))

app = FastAPI(title='Coqui TTS API')
app.mount('/static', StaticFiles(directory='app/static'), name='static')
templates = Jinja2Templates(directory='app/templates')

# Инициализация кэша и TTS сервисов
cache = FileCache(cache_dir='cache', ttl=CACHE_TTL)
# Попытка определить GPU по окружению
use_gpu = os.getenv('USE_GPU', '0') == '1'
tts = TTSService(use_gpu=use_gpu, cache=cache)

# Предзагрузка модели при старте
@app.on_event("startup")
async def startup_event():
    """Предзагрузка модели в память при старте приложения"""
    preload_model = os.getenv('PRELOAD_MODEL', 'xtts-v2')
    if preload_model:
        print(f"\n{'='*60}")
        print(f"🚀 Preloading model: {preload_model}")
        print(f"{'='*60}")
        try:
            # Загружаем модель в память
            tts._get_tts(preload_model)
            print(f"✅ Model {preload_model} preloaded successfully!")
            print(f"{'='*60}\n")
        except Exception as e:
            print(f"⚠️  Failed to preload model {preload_model}: {e}")
            print(f"{'='*60}\n")

@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse('index.html', {
        'request': request,
        'models': tts.get_models()
    })

@app.get('/speakers/{model_id}')
async def get_speakers(model_id: str):
    speakers = tts.get_speakers(model_id)
    return {'speakers': speakers}

@app.post('/synthesize')
async def synthesize(
    text: str = Form(...),
    model_id: str = Form('xtts-v2'),
    language: str = Form('en'),
    speaker: str = Form(None),
    fmt: str = Form('wav')
):
    if not text:
        raise HTTPException(status_code=400, detail='Text is required')
    if len(text) > MAX_TEXT_LENGTH:
        raise HTTPException(status_code=400, detail=f'Max text length is {MAX_TEXT_LENGTH}')

    # Разбиваем текст на части, синтезируем по частям и объединяем
    parts = split_text(text, max_len=MAX_TEXT_LENGTH)
    # Генерируем имя кэша
    cache_key = tts.cache_key(text, model_id=model_id, language=language, speaker=speaker, fmt=fmt)
    
    if cache.exists(cache_key):
        cached_path = cache.path(cache_key)
        return FileResponse(
            cached_path,
            media_type='audio/' + fmt,
            filename=f'{cache_key}.{fmt}'
        )

    # Генерация
    try:
        out_path = tts.synthesize_to_file(parts, model_id=model_id, language=language, speaker=speaker, out_format=fmt)
        cache.put(cache_key, out_path)
        
        return FileResponse(
            out_path,
            media_type='audio/' + fmt,
            filename=os.path.basename(out_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/download/{filename}')
async def download(filename: str):
    filepath = os.path.join('cache', filename)
    if os.path.exists(filepath):
        return FileResponse(
            filepath,
            media_type='application/octet-stream',
            filename=filename
        )
    raise HTTPException(404, detail='File not found')

# Speaker Management Endpoints

@app.get('/speakers', response_class=HTMLResponse)
async def speakers_page(request: Request):
    """Страница управления спикерами"""
    return templates.TemplateResponse('speakers.html', {
        'request': request
    })

@app.post('/api/speakers')
async def create_speaker(
    speaker_id: str = Form(...),
    audio: UploadFile = File(...)
):
    """Создание нового спикера из аудиофайла"""
    try:
        result = tts.create_speaker(speaker_id, audio.file)
        return {'success': True, 'speaker': result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/speakers')
async def list_speakers():
    """Получение списка всех спикеров"""
    speakers = tts.get_all_speakers()
    return {'speakers': speakers}

@app.get('/api/speakers/{speaker_id}')
async def get_speaker_info(speaker_id: str):
    """Получение информации о спикере"""
    speakers = tts.get_all_speakers()
    speaker = next((s for s in speakers if s['speaker_id'] == speaker_id), None)
    if not speaker:
        raise HTTPException(status_code=404, detail='Speaker not found')
    return speaker

@app.delete('/api/speakers/{speaker_id}')
async def delete_speaker(speaker_id: str):
    """Удаление пользовательского спикера"""
    try:
        success = tts.delete_speaker(speaker_id)
        if success:
            return {'success': True, 'message': f'Speaker {speaker_id} deleted'}
        raise HTTPException(status_code=404, detail='Speaker not found')
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/speakers/{speaker_id}/audio')
async def get_speaker_audio(speaker_id: str):
    """Получение reference audio файла спикера"""
    try:
        audio_path = tts.get_speaker_audio_path(speaker_id)
        return FileResponse(
            audio_path,
            media_type='audio/wav',
            filename=f'{speaker_id}.wav'
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='Speaker audio not found')
